"""Shopping lists - private to the owner and the people they shared the list
with (see app/services/list_service.py for the access rules). Creating a
list and sharing it are Gold features; members tick items and add/remove
products both here and in the Telegram bot, on the owner's Gold.

Core logic lives in app/services/list_service.py (shared with the bot).
"""

import html
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.services import list_service, telegram_accounts, telegram_api
from app.services.auth_service import get_current_user
from app.services.list_service import ListError
from app.services.subscription_service import access_payload, can_use_lists
from app.services.telegram_texts import t
from app.services.telegram_ui import list_keyboard, list_message_text
from app.services.translation_service import SUPPORTED_LOCALES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lists", tags=["lists"])

LANG_REGEX = "^(" + "|".join(SUPPORTED_LOCALES) + ")$"


class ListItemIn(BaseModel):
    product_id: str
    name: str
    unit: str = ""


class CreateListRequest(BaseModel):
    session_id: Optional[str] = None
    country: str = "ME"
    items: list[ListItemIn]


class AddItemsRequest(BaseModel):
    items: list[ListItemIn]


class ToggleItemRequest(BaseModel):
    product_id: str


class SaveListRequest(BaseModel):
    name: str


class AddMemberRequest(BaseModel):
    # @username, numeric Telegram id or the email of a site account with
    # Telegram linked. `username` is the old field name (send-telegram).
    identifier: Optional[str] = None
    username: Optional[str] = None
    lang: str = "ukr"


def _raise(err: ListError):
    raise HTTPException(status_code=err.status, detail=err.code)


def _require_gold(user: Optional[dict]) -> dict:
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not can_use_lists(user):
        raise HTTPException(status_code=403, detail="gold_required")
    return user


async def _load(list_id: str, user: Optional[dict]) -> tuple[dict, str]:
    try:
        doc = await list_service.get_list_doc(list_id)
        return doc, list_service.assert_can_view(doc, user)
    except ListError as e:
        _raise(e)


async def _owned(list_id: str, user: Optional[dict]) -> dict:
    user = _require_gold(user)
    doc, role = await _load(list_id, user)
    if role != "owner":
        raise HTTPException(status_code=403, detail="owner_only")
    return doc


async def _payload(doc: dict, user: Optional[dict], lang: str) -> dict:
    resolved = await list_service.resolve_list(doc, lang)
    role = list_service.role_of(doc, user)
    resolved.update({
        "role": role,
        "can_edit": await list_service.can_edit(doc, user),
        "owner_name": await list_service.owner_name(doc),
        "members": await list_service.members_of(doc) if role in ("owner", "admin") else [],
    })
    return resolved


@router.post("")
async def create_list(
    payload: CreateListRequest,
    lang: str = Query("ukr", regex=LANG_REGEX),
    current_user: Optional[dict] = Depends(get_current_user),
):
    user = _require_gold(current_user)
    if not payload.items:
        raise HTTPException(status_code=400, detail="List must have at least one item")
    if payload.country not in ("ME", "UA"):
        raise HTTPException(status_code=400, detail="Unknown country")
    try:
        doc = await list_service.create_list(
            user["_id"], [i.model_dump() for i in payload.items], payload.country, session_id=payload.session_id
        )
    except ListError as e:
        _raise(e)
    return await _payload(doc, user, lang)


@router.get("/mine")
async def my_lists(current_user: Optional[dict] = Depends(get_current_user)):
    """Own lists and lists shared with the user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    docs = await list_service.accessible_lists(current_user["_id"])
    lists = []
    for doc in docs:
        own = doc.get("owner_user_id") == current_user["_id"]
        lists.append({
            "id": doc["_id"],
            "name": doc.get("name"),
            "country": doc.get("country"),
            "item_count": len(doc["items"]),
            "updated_at": doc["updated_at"].isoformat(),
            "role": "owner" if own else "member",
            "owner_name": None if own else await list_service.owner_name(doc),
            "member_count": len(doc.get("member_user_ids") or []),
        })
    return {"lists": lists, "limit": await list_service.gold_list_limit(), "access": access_payload(current_user)}


@router.post("/{list_id}/save")
async def save_list(
    list_id: str,
    payload: SaveListRequest,
    lang: str = Query("ukr", regex=LANG_REGEX),
    current_user: Optional[dict] = Depends(get_current_user),
):
    user = _require_gold(current_user)
    try:
        doc = await list_service.save_list(list_id, user["_id"], payload.name.strip()[:100])
    except ListError as e:
        _raise(e)
    return await _payload(doc, user, lang)


@router.get("/{list_id}")
async def get_list(
    list_id: str,
    lang: str = Query("ukr", regex=LANG_REGEX),
    current_user: Optional[dict] = Depends(get_current_user),
):
    doc, _ = await _load(list_id, current_user)
    return await _payload(doc, current_user, lang)


@router.patch("/{list_id}/toggle")
async def toggle_item(
    list_id: str,
    payload: ToggleItemRequest,
    lang: str = Query("ukr", regex=LANG_REGEX),
    current_user: Optional[dict] = Depends(get_current_user),
):
    await _load(list_id, current_user)
    try:
        doc = await list_service.toggle_item(list_id, product_id=payload.product_id)
    except ListError as e:
        _raise(e)
    return await _payload(doc, current_user, lang)


async def _editable(list_id: str, user: Optional[dict]) -> dict:
    doc, _ = await _load(list_id, user)
    try:
        await list_service.assert_can_edit(doc, user)
    except ListError as e:
        _raise(e)
    return doc


@router.post("/{list_id}/items")
async def add_item(
    list_id: str,
    item: ListItemIn,
    lang: str = Query("ukr", regex=LANG_REGEX),
    current_user: Optional[dict] = Depends(get_current_user),
):
    await _editable(list_id, current_user)
    doc = await list_service.add_items(list_id, [item.model_dump()])
    return await _payload(doc, current_user, lang)


@router.post("/{list_id}/items/bulk")
async def add_items(
    list_id: str,
    payload: AddItemsRequest,
    lang: str = Query("ukr", regex=LANG_REGEX),
    current_user: Optional[dict] = Depends(get_current_user),
):
    await _editable(list_id, current_user)
    doc = await list_service.add_items(list_id, [i.model_dump() for i in payload.items[:100]])
    return await _payload(doc, current_user, lang)


@router.delete("/{list_id}/items/{product_id}")
async def remove_item(
    list_id: str,
    product_id: str,
    lang: str = Query("ukr", regex=LANG_REGEX),
    current_user: Optional[dict] = Depends(get_current_user),
):
    await _editable(list_id, current_user)
    doc = await list_service.remove_item(list_id, product_id)
    return await _payload(doc, current_user, lang)


# --- sharing -----------------------------------------------------------------

@router.post("/{list_id}/members")
async def add_member(
    list_id: str,
    payload: AddMemberRequest,
    lang: str = Query("ukr", regex=LANG_REGEX),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """Shares the list with a Telegram user and sends it to them in the bot.
    Telegram only lets a bot message people who have started it, so the
    recipient must have opened the bot at least once - otherwise
    `telegram_user_not_found`, and the UI offers an invitation link."""
    doc = await _owned(list_id, current_user)
    identifier = (payload.identifier or payload.username or "").strip()
    recipient = await telegram_accounts.find_user_by_identifier(identifier) if identifier else None
    if not recipient or not recipient.get("telegram_id"):
        raise HTTPException(status_code=404, detail="telegram_user_not_found")
    if recipient["_id"] == current_user["_id"]:
        raise HTTPException(status_code=400, detail="cannot_share_with_self")

    doc, _ = await list_service.add_member(list_id, recipient["_id"])
    bot_lang = recipient.get("bot_lang") or payload.lang
    resolved = await list_service.resolve_list(doc, bot_lang)
    sender = list_service._display(current_user)
    text = t(bot_lang, "list_received", sender=html.escape(sender)) + "\n\n" + list_message_text(resolved, bot_lang)
    sent = await telegram_api.send_message(recipient["telegram_id"], text, list_keyboard(resolved, bot_lang, role="member"))
    if not sent:
        logger.warning(f"List {list_id} shared with {recipient['_id']} but the Telegram message failed")
    return {**await _payload(doc, current_user, lang), "notified": bool(sent)}


# Old name of the endpoint above (the site's first sharing form).
router.add_api_route("/{list_id}/send-telegram", add_member, methods=["POST"])


@router.delete("/{list_id}/members/{user_id}")
async def remove_member(
    list_id: str,
    user_id: str,
    lang: str = Query("ukr", regex=LANG_REGEX),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """The owner removes someone, or a member leaves (user_id = own id)."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    doc, role = await _load(list_id, current_user)
    if role != "owner" and user_id != current_user["_id"]:
        raise HTTPException(status_code=403, detail="owner_only")
    doc = await list_service.remove_member(list_id, user_id)
    if user_id == current_user["_id"]:
        return {"ok": True, "left": True}
    return await _payload(doc, current_user, lang)


@router.post("/{list_id}/invite")
async def create_invite(list_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """A single-use invitation link (7 days): whoever opens it in the bot
    joins the list."""
    await _owned(list_id, current_user)
    token = await list_service.create_invite(list_id, current_user["_id"])
    return {"token": token, "url": telegram_api.bot_link(f"join_{token}")}
