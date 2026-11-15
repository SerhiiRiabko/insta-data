"""Minimal outgoing Telegram Bot API client for the web API process.

The bot process (backend/bot/) owns getUpdates polling via aiogram. The API
process only needs to *send* things - admin notifications about card
transfers, Stars invoice links for site purchases, a shared list to a
Telegram user - so it calls the Bot API directly over HTTPS instead of
importing aiogram's runtime. Never raises: Telegram being down must not
break a site request.
"""

import logging
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def bot_link(start_payload: Optional[str] = None) -> str:
    url = f"https://t.me/{settings.telegram_bot_username}"
    return f"{url}?start={start_payload}" if start_payload else url


async def call(method: str, **params: Any) -> Optional[Any]:
    """Calls a Bot API method; returns `result` or None on any failure."""
    if not settings.telegram_bot_token:
        logger.warning(f"telegram_api.{method}: TELEGRAM_BOT_TOKEN not configured")
        return None
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"
    payload = {k: v for k, v in params.items() if v is not None}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
        data = response.json()
        if not data.get("ok"):
            logger.warning(f"telegram_api.{method} failed: {data.get('description')}")
            return None
        return data.get("result")
    except Exception as e:
        logger.warning(f"telegram_api.{method} error: {e}")
        return None


async def send_message(chat_id: int, text: str, reply_markup: Optional[dict] = None) -> Optional[dict]:
    return await call(
        "sendMessage",
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        reply_markup=reply_markup,
        link_preview_options={"is_disabled": True},
    )


async def edit_message_text(chat_id: int, message_id: int, text: str, reply_markup: Optional[dict] = None) -> Optional[dict]:
    return await call(
        "editMessageText",
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=reply_markup,
        link_preview_options={"is_disabled": True},
    )


async def create_stars_subscription_link(title: str, description: str, payload: str, stars: int, period_seconds: int) -> Optional[str]:
    """Stars (XTR) subscription invoice link - renews monthly on the payer's
    side until they cancel it in Telegram. No provider token for Stars."""
    return await call(
        "createInvoiceLink",
        title=title,
        description=description,
        payload=payload,
        currency="XTR",
        prices=[{"label": title, "amount": stars}],
        subscription_period=period_seconds,
    )
