"""Telegram notifications around card-transfer requests. Used by both the
API (request created on the site, admin decides in the admin panel) and the
bot (request created in the bot, admin decides with the inline buttons), so
everything goes through the raw Bot API client."""

import html
import logging
from typing import Optional

from app.database.mongodb import get_mongo_db
from app.services import telegram_api
from app.services.subscription_service import plan_expires_at
from app.services.telegram_accounts import admin_chat_ids
from app.services.telegram_texts import format_date, plan_name, t
from app.core.config import settings

logger = logging.getLogger(__name__)

STATUS_LABEL = {"approved": "✅ Підтверджено", "declined": "❌ Відхилено"}


def describe_user(user: dict) -> str:
    parts = []
    if user.get("email"):
        parts.append(user["email"])
    if user.get("telegram_username"):
        parts.append(f"@{user['telegram_username']}")
    elif user.get("telegram_first_name"):
        parts.append(user["telegram_first_name"])
    if user.get("telegram_id"):
        parts.append(f"tg:{user['telegram_id']}")
    return " · ".join(parts) or user["_id"]


def _admin_text(request: dict, user: Optional[dict]) -> str:
    lines = [
        "💳 <b>Запит на оплату карткою</b>",
        f"Користувач: {html.escape(describe_user(user)) if user else request['user_id']}",
        f"Тариф: {plan_name('ukr', request['plan'])} · {request['amount_eur']} €",
    ]
    if request.get("comment"):
        lines.append(f"Коментар: {html.escape(request['comment'])}")
    if request["status"] != "pending":
        lines.append(f"\n{STATUS_LABEL[request['status']]}")
    return "\n".join(lines)


async def notify_admins_new_request(request: dict) -> None:
    db = get_mongo_db()
    user = await db.users.find_one({"_id": request["user_id"]})
    keyboard = {"inline_keyboard": [[
        {"text": "✅ Підтвердити", "callback_data": f"pr:a:{request['_id']}"},
        {"text": "❌ Відхилити", "callback_data": f"pr:d:{request['_id']}"},
    ]]}
    sent = []
    for chat_id in await admin_chat_ids():
        message = await telegram_api.send_message(chat_id, _admin_text(request, user), keyboard)
        if message:
            sent.append({"chat_id": chat_id, "message_id": message["message_id"]})
    if sent:
        await db.payment_requests.update_one({"_id": request["_id"]}, {"$set": {"admin_messages": sent}})
    else:
        logger.warning(
            f"Payment request {request['_id']}: no admin Telegram chat to notify - "
            "it is still visible in the admin panel (Оплати tab)"
        )


async def notify_request_decided(request: dict) -> None:
    """Updates every admin's copy of the request and tells the payer."""
    db = get_mongo_db()
    user = await db.users.find_one({"_id": request["user_id"]})
    for ref in request.get("admin_messages") or []:
        await telegram_api.edit_message_text(ref["chat_id"], ref["message_id"], _admin_text(request, user))

    if not user or not user.get("telegram_id"):
        return
    lang = user.get("bot_lang")
    plan = plan_name(lang, request["plan"])
    if request["status"] == "approved":
        expires = plan_expires_at(user)
        text = t(lang, "payment_approved", plan=plan, date=format_date(expires) if expires else "—")
    else:
        support = settings.admin_telegram_usernames.split(",")[0].strip().lstrip("@")
        text = t(lang, "payment_declined", plan=plan, support=support)
    await telegram_api.send_message(user["telegram_id"], text)
