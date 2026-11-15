"""Shopping lists — creating, saving and sharing are Gold features; viewing
and ticking items off stay open to anyone with the link (the list id is the
shareable capability, same as before), so a Gold user can share a list with
family members who don't pay.

Core logic lives in app/services/list_service.py (shared with the bot).
"""

import html
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.database.mongodb import get_mongo_db
from app.services import list_service, telegram_api
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


class ToggleItemRequest(BaseModel):
    product_id: str


class SaveListRequest(BaseModel):
    name: str


class SendTelegramRequest(BaseModel):
    username: str
    lang: str = "ukr"


def _raise(err: ListError):
    raise HTTPException(status_code=err.status, detail=err.code)


def _require_gold(user: Optional[dict]) -> dict:
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not can_use_lists(user):
        raise HTTPException(status_code=403, detail="gold_required")
    return user


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
    return await list_service.resolve_list(doc, lang)


@router.get("/mine")
async def my_lists(current_user: Optional[dict] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    docs = await list_service.owned_lists(current_user["_id"])
    return {
        "lists": [
            {
                "id": doc["_id"],
                "name": doc.get("name"),
                "country": doc.get("country"),
                "item_count": len(doc["items"]),
                "updated_at": doc["updated_at"].isoformat(),
            }
            for doc in docs
        ],
        "limit": await list_service.gold_list_limit(),
        "access": access_payload(current_user),
    }


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
    return await list_service.resolve_list(doc, lang)


@router.get("/{list_id}")
async def get_list(list_id: str, lang: str = Query("ukr", regex=LANG_REGEX)):
    try:
        doc = await list_service.get_list_doc(list_id)
    except ListError as e:
        _raise(e)
    return await list_service.resolve_list(doc, lang)


@router.patch("/{list_id}/toggle")
async def toggle_item(list_id: str, payload: ToggleItemRequest, lang: str = Query("ukr", regex=LANG_REGEX)):
    try:
        doc = await list_service.toggle_item(list_id, product_id=payload.product_id)
    except ListError as e:
        _raise(e)
    return await list_service.resolve_list(doc, lang)


@router.post("/{list_id}/items")
async def add_item(
    list_id: str,
    item: ListItemIn,
    lang: str = Query("ukr", regex=LANG_REGEX),
    current_user: Optional[dict] = Depends(get_current_user),
):
    _require_gold(current_user)
    try:
        doc, _ = await list_service.add_item(list_id, item.product_id, item.name, item.unit)
    except ListError as e:
        _raise(e)
    return await list_service.resolve_list(doc, lang)


@router.delete("/{list_id}/items/{product_id}")
async def remove_item(
    list_id: str,
    product_id: str,
    lang: str = Query("ukr", regex=LANG_REGEX),
    current_user: Optional[dict] = Depends(get_current_user),
):
    _require_gold(current_user)
    try:
        doc = await list_service.remove_item(list_id, product_id)
    except ListError as e:
        _raise(e)
    return await list_service.resolve_list(doc, lang)


@router.post("/{list_id}/send-telegram")
async def send_to_telegram(
    list_id: str,
    payload: SendTelegramRequest,
    current_user: Optional[dict] = Depends(get_current_user),
):
    """Sends the list (with tick-off buttons) to a Telegram user by
    @username. Telegram only lets a bot message people who have started it,
    so the recipient must have opened the bot at least once - otherwise the
    caller gets `telegram_user_not_found` and the UI offers the plain
    t.me/share link instead."""
    user = _require_gold(current_user)
    try:
        doc = await list_service.get_list_doc(list_id)
    except ListError as e:
        _raise(e)

    username = payload.username.strip().lstrip("@").lower()
    recipient = await get_mongo_db().users.find_one(
        {"telegram_username_lc": username, "telegram_id": {"$type": "number"}}
    ) if username else None
    if not recipient:
        raise HTTPException(status_code=404, detail="telegram_user_not_found")

    lang = recipient.get("bot_lang") or payload.lang
    resolved = await list_service.resolve_list(doc, lang)
    sender = user.get("telegram_first_name") or user.get("email") or "Shop Price Online"
    text = t(lang, "list_received", sender=html.escape(sender)) + "\n\n" + list_message_text(resolved, lang)
    sent = await telegram_api.send_message(recipient["telegram_id"], text, list_keyboard(resolved, lang, owner=False))
    if not sent:
        raise HTTPException(status_code=502, detail="telegram_send_failed")
    return {"ok": True}
