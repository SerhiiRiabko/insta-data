"""Bot behaviour.

Search (private chat, any text that isn't a command):
- free:    "milk" -> a message with one button per store that sells a match.
           Tapping a store turns that message into the store's prices (the
           buttons disappear) and deletes the previous answer, so only one
           store's prices are ever on screen. Another store = search again.
- compare/gold: the same query shows every store side by side; gold also
           gets ➕ buttons that add a product to the shopping list.

Plans (/plan): Telegram Stars subscriptions (30 days, auto-renew) - the
only payment method inside the bot (Telegram's rule for digital goods).
Card transfers are offered on the website; admins approve them here
(pr: buttons). One account for bot + site, see app/services/telegram_accounts.py.

Lists (/lists): private to the owner and the people it's shared with (see
app/services/list_service.py). The owner (Gold) invites with a single-use
link (👥, start=join_<token>), from the website by @username, or posts the
list into a chat via inline mode - people in that chat join by tapping it.
Members tick items and fill the list from search (➕ adds to the list opened
last); the state is the same list the website shows.

callback_data prefixes: c country, l language, ss store pick, sa add to
list, plan, buy Stars payment, lo open list, lt toggle list item, li invite,
lx leave a list, lk/lg confirm link/login, pr admin decision on a card payment.
"""

import html
import logging
import secrets
from datetime import datetime
from urllib.parse import urlencode
from typing import Any, Awaitable, Callable, Optional

from aiogram import BaseMiddleware, Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultsButton,
    InputTextMessageContent,
    Message,
    PreCheckoutQuery,
    TelegramObject,
)

from app.api.v1.endpoints.products import get_stores_for_country
from app.core.config import settings
from app.database.mongodb import get_mongo_db
from app.services import list_service, telegram_accounts, telegram_api
from app.services.list_service import ListError
from app.services.payment_notifications import describe_user, notify_request_decided
from app.services.product_query import in_store, search_country, store_counts
from app.services.subscription_service import (
    FOREVER,
    PAID_PLANS,
    STARS_SUBSCRIPTION_PERIOD_SECONDS,
    can_compare,
    can_use_lists,
    decide_payment_request,
    effective_plan,
    get_plan_settings,
    grant_plan,
    parse_stars_payload,
    plan_expires_at,
    record_stars_payment,
    revoke_plan,
    stars_invoice_payload,
)
from app.services.telegram_accounts import LinkError
from app.services.telegram_texts import (
    BOT_LANGS,
    LANG_NAMES,
    country_name,
    format_date,
    format_price,
    plan_name,
    t,
)
from app.services.telegram_ui import list_keyboard, list_message_text
from app.services.translation_service import resolve_display_name

logger = logging.getLogger(__name__)
router = Router()

RESULTS_PER_MESSAGE = 10


def kb(rows: list[list[dict]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.model_validate({"inline_keyboard": rows})


def lang_of(user: Optional[dict]) -> str:
    return (user or {}).get("bot_lang") or "eng"


def support_username() -> str:
    return settings.admin_telegram_usernames.split(",")[0].strip().lstrip("@")


def tg_dict(tg) -> dict:
    return {"id": tg.id, "username": tg.username, "first_name": tg.first_name, "language_code": tg.language_code}


async def set_user(user: dict, **fields) -> None:
    await get_mongo_db().users.update_one({"_id": user["_id"]}, {"$set": fields})
    user.update(fields)


async def safe_delete(bot: Bot, chat_id: int, message_id: Optional[int]) -> None:
    if not message_id:
        return
    try:
        await bot.delete_message(chat_id, message_id)
    except TelegramBadRequest:
        pass  # already gone, or older than Telegram's 48h delete window


class UserMiddleware(BaseMiddleware):
    """Loads (or creates) the `users` document of whoever sent the update
    and passes it to handlers as `user`."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg = getattr(event, "from_user", None)
        data["user"] = (
            await telegram_accounts.get_or_create_telegram_user(tg_dict(tg)) if tg and not tg.is_bot else None
        )
        return await handler(event, data)


# ---------------------------------------------------------------------------
# Start, settings
# ---------------------------------------------------------------------------

def country_keyboard(lang: str) -> InlineKeyboardMarkup:
    return kb([[{"text": country_name(lang, c), "callback_data": f"c:{c}"}] for c in ("UA", "ME")])


async def ask_country(message: Message, user: dict) -> None:
    await message.answer(t(lang_of(user), "choose_country"), reply_markup=country_keyboard(lang_of(user)))


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, user: dict, bot: Bot):
    payload = command.args or ""
    if payload.startswith("link_"):
        return await start_link(message, user, payload[len("link_"):])
    if payload.startswith("login_"):
        return await start_login(message, user, payload[len("login_"):])
    if payload.startswith("list_"):
        return await send_list(message, user, payload[len("list_"):])
    if payload.startswith("join_"):
        return await join_list(message, user, bot, payload[len("join_"):])
    if payload == "plan":
        return await show_plans(message, user)

    await message.answer(t(lang_of(user), "welcome"))
    if not user.get("country"):
        await ask_country(message, user)


@router.message(Command("help"))
async def cmd_help(message: Message, user: dict):
    await message.answer(t(lang_of(user), "help"))


@router.message(Command("paysupport"))
async def cmd_paysupport(message: Message, user: dict):
    await message.answer(t(lang_of(user), "paysupport", support=support_username()))


@router.message(Command("country"))
async def cmd_country(message: Message, user: dict):
    await ask_country(message, user)


@router.callback_query(F.data.startswith("c:"))
async def on_country(callback: CallbackQuery, user: dict, bot: Bot):
    country = callback.data.split(":", 1)[1]
    if country not in ("UA", "ME"):
        return await callback.answer()
    lang = lang_of(user)
    await set_user(user, country=country)
    await callback.message.edit_text(t(lang, "country_set", country=country_name(lang, country)))
    await callback.answer()
    pending = user.get("pending_query")
    if pending:
        await set_user(user, pending_query=None)
        await run_search(callback.message.chat.id, bot, user, pending)


@router.message(Command("lang"))
async def cmd_lang(message: Message, user: dict):
    rows = [[{"text": LANG_NAMES[code], "callback_data": f"l:{code}"}] for code in BOT_LANGS]
    await message.answer(t(lang_of(user), "choose_lang"), reply_markup=kb(rows))


@router.callback_query(F.data.startswith("l:"))
async def on_lang(callback: CallbackQuery, user: dict):
    code = callback.data.split(":", 1)[1]
    if code in BOT_LANGS:
        await set_user(user, bot_lang=code)
        await callback.message.edit_text(t(code, "lang_set"))
    await callback.answer()


@router.message(Command("site"))
async def cmd_site(message: Message, user: dict):
    lang = lang_of(user)
    token = await telegram_accounts.create_token("web_login", user_id=user["_id"], lang=lang)
    url = f"{settings.backend_url.rstrip('/')}/api/v1/auth/telegram/web?token={token}"
    if any(host in url for host in ("://localhost", "://127.0.0.1")):
        # Telegram rejects localhost URL buttons; plain text still works in dev.
        return await message.answer(f"{t(lang, 'site_login')}\n{url}")
    await message.answer(t(lang, "site_login"), reply_markup=kb([[{"text": t(lang, "btn_open_site"), "url": url}]]))


# ---------------------------------------------------------------------------
# Account linking / Telegram login (deep links from the website)
# ---------------------------------------------------------------------------

async def start_link(message: Message, user: dict, token: str) -> None:
    lang = lang_of(user)
    doc = await telegram_accounts.get_token(token, "link")
    account = await get_mongo_db().users.find_one({"_id": doc["user_id"]}) if doc and doc["status"] == "pending" else None
    if not account:
        await message.answer(t(lang, "token_invalid"))
        return
    await message.answer(
        t(lang, "link_confirm", account=html.escape(account.get("email") or "—")),
        reply_markup=kb([[
            {"text": t(lang, "btn_confirm"), "callback_data": f"lk:{token}:y"},
            {"text": t(lang, "btn_cancel"), "callback_data": f"lk:{token}:n"},
        ]]),
    )


@router.callback_query(F.data.startswith("lk:"))
async def on_link_confirm(callback: CallbackQuery, user: dict):
    _, token, answer = callback.data.split(":")
    lang = lang_of(user)
    await callback.answer()
    if answer != "y":
        await callback.message.edit_text(t(lang, "cancelled"))
        return

    doc = await telegram_accounts.confirm_token(token, "link", telegram_id=callback.from_user.id)
    if not doc:
        await callback.message.edit_text(t(lang, "token_invalid"))
        return
    try:
        linked = await telegram_accounts.link_telegram(doc["user_id"], tg_dict(callback.from_user))
    except LinkError as e:
        await get_mongo_db().telegram_tokens.update_one({"_id": token}, {"$set": {"status": "failed", "error": e.code}})
        await callback.message.edit_text(t(lang, "link_elsewhere" if e.code == "telegram_linked_elsewhere" else "token_invalid"))
        return

    await get_mongo_db().telegram_tokens.update_one({"_id": token}, {"$set": {"status": "linked"}})
    lang = linked.get("bot_lang") or lang
    await callback.message.edit_text(t(lang, "link_done", account=html.escape(linked.get("email") or "")))
    if doc.get("plan") in PAID_PLANS:
        await send_stars_offer(callback.message, linked, doc["plan"])


async def start_login(message: Message, user: dict, token: str) -> None:
    lang = lang_of(user)
    doc = await telegram_accounts.get_token(token, "login")
    if not doc or doc["status"] != "pending":
        await message.answer(t(lang, "token_invalid"))
        return
    await message.answer(
        t(lang, "login_confirm"),
        reply_markup=kb([[
            {"text": t(lang, "btn_confirm"), "callback_data": f"lg:{token}:y"},
            {"text": t(lang, "btn_cancel"), "callback_data": f"lg:{token}:n"},
        ]]),
    )


@router.callback_query(F.data.startswith("lg:"))
async def on_login_confirm(callback: CallbackQuery, user: dict):
    _, token, answer = callback.data.split(":")
    lang = lang_of(user)
    await callback.answer()
    if answer != "y":
        await callback.message.edit_text(t(lang, "cancelled"))
        return
    doc = await telegram_accounts.confirm_token(token, "login", user_id=user["_id"], telegram_id=callback.from_user.id)
    await callback.message.edit_text(t(lang, "login_done" if doc else "token_invalid"))


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@router.message(F.chat.type == "private", F.text, ~F.text.startswith("/"))
async def on_text(message: Message, user: dict, bot: Bot):
    if message.via_bot:
        return  # one of our own inline results posted into this chat
    query = message.text.strip()[:100]
    if not user.get("country"):
        await set_user(user, pending_query=query)
        await ask_country(message, user)
        return
    await run_search(message.chat.id, bot, user, query)


def _padded(prices: Optional[list], size: int) -> list:
    return ((prices or []) + [None] * size)[:size]


def _unit(doc: dict) -> str:
    return f" · {html.escape(doc['unit'])}" if doc.get("unit") else ""


def compare_text(docs: list[dict], stores: list[dict], query: str, lang: str, country: str, gold: bool) -> str:
    lines = [t(lang, "compare_result", q=html.escape(query)), ""]
    for n, doc in enumerate(docs[:RESULTS_PER_MESSAGE], start=1):
        prices = _padded(doc.get("prices"), len(stores))
        promo = _padded(doc.get("promo"), len(stores))
        pairs = sorted((p, i) for i, p in enumerate(prices) if p is not None)
        parts = []
        for rank, (price, i) in enumerate(pairs):
            mark = "✅ " if rank == 0 and len(pairs) > 1 else ""
            parts.append(f"{mark}{html.escape(stores[i]['name'])} {format_price(price, country)}{' 🏷' if promo[i] else ''}")
        lines.append(f"{n}. <b>{html.escape(doc['display_name'])}</b>{_unit(doc)}\n      " + " · ".join(parts))
    if len(docs) > RESULTS_PER_MESSAGE:
        lines += ["", t(lang, "more_results", n=len(docs) - RESULTS_PER_MESSAGE)]
    if gold:
        lines += ["", f"<i>{t(lang, 'add_hint')}</i>"]
    return "\n".join(lines)


def store_text(docs: list[dict], stores: list[dict], index: int, query: str, lang: str, country: str) -> str:
    items = in_store(docs, index)
    lines = [t(lang, "store_result", store=html.escape(stores[index]["name"]), q=html.escape(query)), ""]
    for n, (doc, price) in enumerate(items[:RESULTS_PER_MESSAGE], start=1):
        promo = _padded(doc.get("promo"), len(stores))[index]
        lines.append(f"{n}. {html.escape(doc['display_name'])}{_unit(doc)} — <b>{format_price(price, country)}</b>{' 🏷' if promo else ''}")
    if len(items) > RESULTS_PER_MESSAGE:
        lines += ["", t(lang, "more_results", n=len(items) - RESULTS_PER_MESSAGE)]
    lines += ["", f"<i>{t(lang, 'free_footer')}</i>"]
    return "\n".join(lines)


async def run_search(chat_id: int, bot: Bot, user: dict, query: str) -> None:
    lang, country = lang_of(user), user["country"]
    stores = await get_stores_for_country(country)
    docs = [d for d in await search_country(query, country, lang) if any(p is not None for p in _padded(d.get("prices"), len(stores)))]
    if not docs or not stores:
        await bot.send_message(chat_id, t(lang, "no_results", q=html.escape(query)))
        return

    sid = secrets.token_hex(6)
    await get_mongo_db().bot_searches.insert_one({
        "_id": sid,
        "user_id": user["_id"],
        "query": query,
        "country": country,
        "product_ids": [d["id"] for d in docs[:200]],
        "created_at": datetime.utcnow(),
    })

    if can_compare(user):
        can_add = can_use_lists(user) or await list_service.active_list_for(user, country) is not None
        rows = add_buttons(sid, list(range(min(len(docs), RESULTS_PER_MESSAGE)))) if can_add else []
        await bot.send_message(chat_id, compare_text(docs, stores, query, lang, country, can_add), reply_markup=kb(rows) if rows else None)
        return

    counts = store_counts(docs, len(stores))
    buttons = [
        {"text": f"{store['name']} · {counts[i]}", "callback_data": f"ss:{sid}:{i}"}
        for i, store in enumerate(stores) if counts[i] > 0
    ]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    plan_settings = await get_plan_settings()
    rows.append([{"text": t(lang, "btn_unlock_compare", stars=plan_settings["compare_stars"]), "callback_data": "plan"}])

    await safe_delete(bot, chat_id, user.get("bot_choice_msg_id"))
    sent = await bot.send_message(chat_id, t(lang, "choose_store", q=html.escape(query), n=len(docs)), reply_markup=kb(rows))
    await set_user(user, bot_choice_msg_id=sent.message_id)


def add_buttons(sid: str, positions: list[int]) -> list[list[dict]]:
    """➕1 ➕2 … for the numbered results; `positions` index the search's
    product_ids (what sa: callbacks carry)."""
    buttons = [{"text": f"➕{n}", "callback_data": f"sa:{sid}:{pos}"} for n, pos in enumerate(positions, start=1)]
    return [buttons[i:i + 5] for i in range(0, len(buttons), 5)]


async def _search_docs(search: dict, lang: str) -> list[dict]:
    ids = search["product_ids"]
    found = {
        d["id"]: d
        async for d in get_mongo_db().products.find({"id": {"$in": ids}, "country": search["country"]})
    }
    docs = [found[i] for i in ids if i in found]
    for doc in docs:
        doc["display_name"] = resolve_display_name(doc, lang)
    return docs


@router.callback_query(F.data.startswith("ss:"))
async def on_store_pick(callback: CallbackQuery, user: dict, bot: Bot):
    _, sid, index = callback.data.split(":")
    lang = lang_of(user)
    search = await get_mongo_db().bot_searches.find_one({"_id": sid, "user_id": user["_id"]})
    if not search:
        await callback.answer(t(lang, "query_expired"), show_alert=True)
        return
    stores = await get_stores_for_country(search["country"])
    index = int(index)
    if index >= len(stores):
        await callback.answer(t(lang, "query_expired"), show_alert=True)
        return

    docs = await _search_docs(search, lang)
    chat_id = callback.message.chat.id
    previous = user.get("bot_answer_msg_id")
    if previous and previous != callback.message.message_id:
        await safe_delete(bot, chat_id, previous)
    # The store buttons go away; someone filling a (shared) list gets ➕
    # buttons for the products shown instead.
    markup = None
    if await list_service.active_list_for(user, search["country"]) is not None:
        position = {pid: pos for pos, pid in enumerate(search["product_ids"])}
        shown = [position[doc["id"]] for doc, _ in in_store(docs, index)[:RESULTS_PER_MESSAGE]]
        markup = kb(add_buttons(sid, shown))
    await callback.message.edit_text(store_text(docs, stores, index, search["query"], lang, search["country"]), reply_markup=markup)
    await set_user(user, bot_answer_msg_id=callback.message.message_id, bot_choice_msg_id=None)
    await callback.answer()


@router.callback_query(F.data.startswith("sa:"))
async def on_add_to_list(callback: CallbackQuery, user: dict):
    _, sid, position = callback.data.split(":")
    lang = lang_of(user)
    search = await get_mongo_db().bot_searches.find_one({"_id": sid, "user_id": user["_id"]})
    position = int(position)
    if not search or position >= len(search["product_ids"]):
        await callback.answer(t(lang, "query_expired"), show_alert=True)
        return

    product = await get_mongo_db().products.find_one({"id": search["product_ids"][position], "country": search["country"]})
    if not product:
        await callback.answer(t(lang, "query_expired"), show_alert=True)
        return
    try:
        target = await list_service.active_list_for(user, search["country"], t(lang, "list_untitled"))
    except ListError:
        await callback.answer("⚠️", show_alert=True)
        return
    if target is None:
        await callback.answer()
        await send_gold_required(callback.message, user)
        return
    _, added = await list_service.add_item(target["_id"], product["id"], product["name"], product.get("unit", ""))
    name = resolve_display_name(product, lang)
    list_name = target.get("name") or t(lang, "list_untitled")
    await callback.answer(t(lang, "added_to_named_list", item=name[:100], list=list_name[:50]) if added else t(lang, "already_in_list"))


# ---------------------------------------------------------------------------
# Plans and payments
# ---------------------------------------------------------------------------

def plan_status_text(user: dict) -> str:
    lang = lang_of(user)
    plan = effective_plan(user)
    expires = plan_expires_at(user)
    until = ""
    if plan != "free":
        until = t(lang, "plan_forever") if (user.get("is_admin") or not expires or expires >= FOREVER) else t(lang, "plan_until", date=format_date(expires))
    return t(lang, "plan_status", plan=plan_name(lang, plan), until=until)


async def show_plans(message: Message, user: dict) -> None:
    lang = lang_of(user)
    s = await get_plan_settings()
    text = plan_status_text(user) + "\n\n" + t(
        lang, "plans_offer", cs=s["compare_stars"], ce=s["compare_eur"], gs=s["gold_stars"], ge=s["gold_eur"]
    )
    # Stars only inside the bot: Telegram requires digital goods sold in a
    # bot to be paid in Stars, so the card-transfer option lives on the
    # website only (its requests still reach admins here for approval).
    rows = [
        [{"text": t(lang, "btn_stars", plan=plan_name(lang, p), stars=s[f"{p}_stars"]), "callback_data": f"buy:{p}"}]
        for p in PAID_PLANS
    ]
    await message.answer(text, reply_markup=kb(rows))


async def send_gold_required(message: Message, user: dict) -> None:
    lang = lang_of(user)
    s = await get_plan_settings()
    await message.answer(
        t(lang, "gold_required", stars=s["gold_stars"], eur=s["gold_eur"]),
        reply_markup=kb([[{"text": t(lang, "btn_stars", plan=plan_name(lang, "gold"), stars=s["gold_stars"]), "callback_data": "buy:gold"}]]),
    )


async def send_stars_offer(message: Message, user: dict, plan: str) -> None:
    lang = lang_of(user)
    s = await get_plan_settings()
    name = plan_name(lang, plan)
    url = await telegram_api.create_stars_subscription_link(
        title=f"Shop Price Online · {name}",
        description=t(lang, "invoice_description", plan=name),
        payload=stars_invoice_payload(plan, user["_id"]),
        stars=s[f"{plan}_stars"],
        period_seconds=STARS_SUBSCRIPTION_PERIOD_SECONDS,
    )
    if not url:
        await message.answer("⚠️ Telegram payments are unavailable right now, please try later.")
        return
    await message.answer(
        t(lang, "invoice_description", plan=name),
        reply_markup=kb([[{"text": t(lang, "btn_stars", plan=name, stars=s[f"{plan}_stars"]), "url": url}]]),
    )


@router.message(Command("plan"))
async def cmd_plan(message: Message, user: dict):
    await show_plans(message, user)


@router.callback_query(F.data == "plan")
async def on_plan(callback: CallbackQuery, user: dict):
    await callback.answer()
    await show_plans(callback.message, user)


@router.callback_query(F.data.startswith("buy:"))
async def on_buy(callback: CallbackQuery, user: dict):
    plan = callback.data.split(":", 1)[1]
    await callback.answer()
    if plan in PAID_PLANS:
        await send_stars_offer(callback.message, user, plan)


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery):
    parsed = parse_stars_payload(query.invoice_payload)
    ok = bool(parsed) and await get_mongo_db().users.find_one({"_id": parsed[1]}, {"_id": 1}) is not None
    await query.answer(ok=ok, error_message=None if ok else "This order is no longer valid.")


@router.message(F.successful_payment)
async def on_successful_payment(message: Message, user: dict):
    payment = message.successful_payment
    updated = await record_stars_payment(
        charge_id=payment.telegram_payment_charge_id,
        payload=payment.invoice_payload,
        stars=payment.total_amount,
        payer_telegram_id=message.from_user.id,
        subscription_expiration_date=payment.subscription_expiration_date,
        is_recurring=bool(payment.is_recurring),
    )
    if not updated:
        return
    plan = parse_stars_payload(payment.invoice_payload)[0]
    lang = lang_of(user)
    await message.answer(t(lang, "stars_thanks", plan=plan_name(lang, plan), date=format_date(updated[f"{plan}_until"])))


# ---------------------------------------------------------------------------
# Shopping lists
# ---------------------------------------------------------------------------

def list_markup(resolved: dict, lang: str, role: Optional[str]) -> InlineKeyboardMarkup:
    # Only the owner (with Gold) gets the share/invite buttons; admins
    # looking at someone's list get the plain view.
    return kb(list_keyboard(resolved, lang, role=role if role in ("owner", "member") else None)["inline_keyboard"])


async def send_list(message: Message, user: dict, list_id: str, *, intro: str = "") -> None:
    lang = lang_of(user)
    try:
        doc = await list_service.get_list_doc(list_id)
    except ListError:
        await message.answer(t(lang, "token_invalid"))
        return
    role = list_service.role_of(doc, user)
    if role is None:
        await message.answer(t(lang, "list_private"))
        return
    if role == "owner" and not can_use_lists(user):
        role = "owner_expired"
    resolved = await list_service.resolve_list(doc, lang)
    text = list_message_text(resolved, lang)
    if role != "guest" and await list_service.can_edit(doc, user):
        await list_service.set_active_list(user, doc["_id"])
        text += "\n\n" + t(lang, "active_list_hint")
    await message.answer((intro + "\n\n" if intro else "") + text, reply_markup=list_markup(resolved, lang, role))


async def join_list(message: Message, user: dict, bot: Bot, token: str) -> None:
    lang = lang_of(user)
    doc, added = await list_service.join_by_invite(token, user)
    if not doc:
        await message.answer(t(lang, "invite_invalid"))
        return
    owner_name = await list_service.owner_name(doc) or "—"
    if added and doc.get("owner_user_id"):
        owner = await get_mongo_db().users.find_one({"_id": doc["owner_user_id"]})
        if owner and owner.get("telegram_id"):
            owner_lang = lang_of(owner)
            try:
                await bot.send_message(owner["telegram_id"], t(
                    owner_lang, "member_joined",
                    member=html.escape(list_service._display(user)),
                    name=html.escape(doc.get("name") or t(owner_lang, "list_untitled")),
                ))
            except TelegramBadRequest:
                pass
    intro = t(lang, "join_done", owner=html.escape(owner_name)) if added else ""
    await send_list(message, user, doc["_id"], intro=intro)


@router.message(Command("lists"))
async def cmd_lists(message: Message, user: dict):
    lang = lang_of(user)
    docs = await list_service.accessible_lists(user["_id"], limit=30)
    if not docs:
        if can_use_lists(user):
            await message.answer(t(lang, "lists_empty"))
        else:
            await send_gold_required(message, user)
        return
    rows = []
    for doc in docs:
        label = f"{doc.get('name') or t(lang, 'list_untitled')} · {len(doc['items'])}"
        if doc.get("owner_user_id") != user["_id"]:
            label = f"👥 {label} · {t(lang, 'list_shared_by', owner=await list_service.owner_name(doc) or '—')}"
        elif doc.get("member_user_ids"):
            label = f"👥 {label}"
        rows.append([{"text": label[:60], "callback_data": f"lo:{doc['_id']}"}])
    await message.answer(t(lang, "lists_title"), reply_markup=kb(rows))


@router.callback_query(F.data.startswith("lo:"))
async def on_open_list(callback: CallbackQuery, user: dict):
    await callback.answer()
    await send_list(callback.message, user, callback.data.split(":", 1)[1])


@router.callback_query(F.data.startswith("li:"))
async def on_invite(callback: CallbackQuery, user: dict):
    lang = lang_of(user)
    list_id = callback.data.split(":", 1)[1]
    try:
        doc = await list_service.get_list_doc(list_id)
    except ListError:
        await callback.answer("⚠️")
        return
    if list_service.role_of(doc, user) != "owner":
        await callback.answer("⛔", show_alert=True)
        return
    if not can_use_lists(user):
        await callback.answer()
        await send_gold_required(callback.message, user)
        return
    await callback.answer()
    token = await list_service.create_invite(list_id, user["_id"])
    url = telegram_api.bot_link(f"join_{token}")
    name = doc.get("name") or t(lang, "list_untitled")
    share = "https://t.me/share/url?" + urlencode({"url": url, "text": t(lang, "invite_share_text", name=name)})
    await callback.message.answer(
        t(lang, "invite_text", name=html.escape(name), url=url),
        reply_markup=kb([[{"text": t(lang, "btn_send_invite"), "url": share}]]),
        disable_web_page_preview=True,
    )


@router.callback_query(F.data.startswith("lx:"))
async def on_leave(callback: CallbackQuery, user: dict):
    lang = lang_of(user)
    list_id = callback.data.split(":", 1)[1]
    await list_service.remove_member(list_id, user["_id"])
    if user.get("active_list_id") == list_id:
        await set_user(user, active_list_id=None)
    await callback.answer()
    try:
        await callback.message.edit_text(t(lang, "left_list"), reply_markup=None)
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("lt:"))
async def on_toggle_item(callback: CallbackQuery, user: Optional[dict], bot: Bot):
    _, list_id, index = callback.data.split(":")
    lang = lang_of(user)
    try:
        doc = await list_service.get_list_doc(list_id)
    except ListError:
        await callback.answer("⚠️")
        return

    if list_service.role_of(doc, user) is None:
        # Someone in a chat the list was posted into: send them to the bot,
        # where the chat invitation adds them (only the people of that chat
        # ever see it). Anywhere else - no access.
        if callback.inline_message_id and doc.get("chat_invite_token"):
            await callback.answer(url=telegram_api.bot_link(f"join_{doc['chat_invite_token']}"))
        else:
            await callback.answer(t(lang, "list_private"), show_alert=True)
        return

    try:
        doc = await list_service.toggle_item(list_id, index=int(index))
    except ListError:
        await callback.answer("⚠️")
        return

    if callback.inline_message_id:
        # Posted into some chat via inline mode: everyone there sees one
        # message, so render it in the owner's language, without owner tools.
        owner = await get_mongo_db().users.find_one({"_id": doc.get("owner_user_id")}) if doc.get("owner_user_id") else None
        lang = lang_of(owner or user)
        resolved = await list_service.resolve_list(doc, lang)
        join_url = telegram_api.bot_link(f"join_{doc['chat_invite_token']}") if doc.get("chat_invite_token") else None
        markup = kb(list_keyboard(resolved, lang, role="chat", join_url=join_url)["inline_keyboard"])
        try:
            await bot.edit_message_text(text=list_message_text(resolved, lang), inline_message_id=callback.inline_message_id, reply_markup=markup)
        except TelegramBadRequest:
            pass
    else:
        resolved = await list_service.resolve_list(doc, lang)
        role = list_service.role_of(doc, user)
        if role == "owner" and not can_use_lists(user):
            role = "owner_expired"
        try:
            await callback.message.edit_text(list_message_text(resolved, lang), reply_markup=list_markup(resolved, lang, role))
        except TelegramBadRequest:
            pass
    await callback.answer()


@router.inline_query()
async def on_inline_query(query: InlineQuery, user: dict):
    lang = lang_of(user)
    if not can_use_lists(user):
        await query.answer(
            [], cache_time=0, is_personal=True,
            button=InlineQueryResultsButton(text=t(lang, "inline_need_gold"), start_parameter="plan"),
        )
        return

    docs = await list_service.owned_lists(user["_id"], limit=20)
    wanted = query.query.strip()
    if wanted.startswith("list "):
        wanted_id = wanted[len("list "):].strip()
        docs.sort(key=lambda d: d["_id"] != wanted_id)

    results = []
    for doc in docs:
        resolved = await list_service.resolve_list(doc, lang)
        join_url = telegram_api.bot_link(f"join_{await list_service.chat_invite(doc)}")
        results.append(InlineQueryResultArticle(
            id=doc["_id"],
            title=doc.get("name") or t(lang, "list_untitled"),
            description=f"{len(resolved['items'])} · {format_price(resolved['total_cheapest'], resolved['country'])}",
            input_message_content=InputTextMessageContent(message_text=list_message_text(resolved, lang), parse_mode="HTML"),
            reply_markup=kb(list_keyboard(resolved, lang, role="chat", join_url=join_url)["inline_keyboard"]),
        ))
    await query.answer(results, cache_time=0, is_personal=True)


# ---------------------------------------------------------------------------
# Admin (Ukrainian only)
# ---------------------------------------------------------------------------

def admin_only(user: Optional[dict]) -> bool:
    return bool(user) and telegram_accounts.is_bot_admin(user)


@router.callback_query(F.data.startswith("pr:"))
async def on_payment_decision(callback: CallbackQuery, user: dict):
    if not admin_only(user):
        await callback.answer("⛔", show_alert=True)
        return
    _, decision, request_id = callback.data.split(":")
    request = await decide_payment_request(request_id, decision == "a", user["_id"])
    if not request:
        await callback.answer("Запит уже оброблено", show_alert=True)
        return
    await notify_request_decided(request)
    await callback.answer("✅ Підтверджено" if decision == "a" else "❌ Відхилено")


ADMIN_HELP = (
    "Адмін-команди:\n"
    "/grant &lt;email | @username | tg_id&gt; [gold|compare] [місяців|forever] — видати тариф (за замовчуванням Gold на 1 місяць)\n"
    "/revoke &lt;email | @username | tg_id&gt; [gold|compare] — забрати тариф\n"
    "/pending — запити на оплату карткою\n"
    "/refund &lt;charge_id&gt; — повернути зірки й забрати тариф\n"
    "/stats — статистика"
)


@router.message(Command("admin"))
async def cmd_admin(message: Message, user: dict):
    if admin_only(user):
        await message.answer(ADMIN_HELP)


@router.message(Command("grant"))
async def cmd_grant(message: Message, command: CommandObject, user: dict):
    if not admin_only(user):
        return
    args = (command.args or "").split()
    if not args:
        await message.answer(ADMIN_HELP)
        return
    plan = next((a for a in args[1:] if a in PAID_PLANS), "gold")
    months: Optional[int] = 1
    for a in args[1:]:
        if a.lower() == "forever":
            months = None
        elif a.isdigit():
            months = int(a)
    target = await telegram_accounts.find_user_by_identifier(args[0])
    if not target:
        await message.answer("Користувача не знайдено. Telegram-користувач має хоч раз запустити бота; email — бути зареєстрованим (або видайте через адмінку сайту — там тариф чекатиме реєстрації).")
        return
    updated = await grant_plan(target["_id"], plan, source="admin", days=months * 30 if months else None)
    until = updated[f"{plan}_until"]
    await message.answer(f"✅ {html.escape(describe_user(updated))}: {plan_name('ukr', plan)} {'безстроково' if until >= FOREVER else 'до ' + format_date(until)}")
    if updated.get("telegram_id") and updated["telegram_id"] != message.from_user.id:
        lang = lang_of(updated)
        await telegram_api.send_message(
            updated["telegram_id"],
            t(lang, "payment_approved", plan=plan_name(lang, plan), date="∞" if until >= FOREVER else format_date(until)),
        )


@router.message(Command("revoke"))
async def cmd_revoke(message: Message, command: CommandObject, user: dict):
    if not admin_only(user):
        return
    args = (command.args or "").split()
    if not args:
        await message.answer(ADMIN_HELP)
        return
    plan = next((a for a in args[1:] if a in PAID_PLANS), None)
    target = await telegram_accounts.find_user_by_identifier(args[0])
    if not target:
        await message.answer("Користувача не знайдено.")
        return
    await revoke_plan(target["_id"], plan)
    await message.answer(f"Тариф {'усі' if not plan else plan_name('ukr', plan)} забрано: {html.escape(describe_user(target))}")


@router.message(Command("pending"))
async def cmd_pending(message: Message, user: dict):
    if not admin_only(user):
        return
    db = get_mongo_db()
    requests = await db.payment_requests.find({"status": "pending"}).sort("created_at", 1).to_list(length=20)
    if not requests:
        await message.answer("Немає запитів, що очікують.")
        return
    for request in requests:
        payer = await db.users.find_one({"_id": request["user_id"]})
        await message.answer(
            f"💳 {html.escape(describe_user(payer) if payer else request['user_id'])}\n"
            f"{plan_name('ukr', request['plan'])} · {request['amount_eur']} € · {format_date(request['created_at'])}\n"
            f"{html.escape(request.get('comment') or '')}",
            reply_markup=kb([[
                {"text": "✅ Підтвердити", "callback_data": f"pr:a:{request['_id']}"},
                {"text": "❌ Відхилити", "callback_data": f"pr:d:{request['_id']}"},
            ]]),
        )


@router.message(Command("refund"))
async def cmd_refund(message: Message, command: CommandObject, user: dict, bot: Bot):
    if not admin_only(user):
        return
    charge_id = (command.args or "").strip()
    payment = await get_mongo_db().payments.find_one({"_id": charge_id}) if charge_id else None
    if not payment:
        await message.answer("Платіж не знайдено. Формат: /refund &lt;telegram_payment_charge_id&gt;")
        return
    try:
        await bot.refund_star_payment(user_id=payment["payer_telegram_id"], telegram_payment_charge_id=charge_id)
    except TelegramBadRequest as e:
        await message.answer(f"Telegram відмовив: {html.escape(str(e))}")
        return
    await revoke_plan(payment["user_id"], payment["plan"], source="refund")
    await get_mongo_db().payments.update_one({"_id": charge_id}, {"$set": {"refunded_at": datetime.utcnow()}})
    await message.answer(f"↩️ Повернуто {payment['stars']}⭐, тариф {plan_name('ukr', payment['plan'])} забрано.")


@router.message(Command("stats"))
async def cmd_stats(message: Message, user: dict):
    if not admin_only(user):
        return
    db = get_mongo_db()
    now = datetime.utcnow()
    total = await db.users.count_documents({})
    telegram = await db.users.count_documents({"telegram_id": {"$type": "number"}})
    gold = await db.users.count_documents({"gold_until": {"$gt": now}})
    compare = await db.users.count_documents({"compare_until": {"$gt": now}, "gold_until": {"$not": {"$gt": now}}})
    stars = sum([p["stars"] async for p in db.payments.find({"method": "stars", "refunded_at": None}, {"stars": 1})])
    pending = await db.payment_requests.count_documents({"status": "pending"})
    await message.answer(
        f"👥 Користувачів: {total} (з Telegram: {telegram})\n"
        f"⭐ Gold: {gold} · Порівняння: {compare}\n"
        f"💰 Зірок отримано: {stars}\n"
        f"💳 Запитів на перевірку: {pending}"
    )
