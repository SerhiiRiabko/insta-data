"""Telegram message + inline-keyboard builders shared by the bot process
(aiogram) and the API process (raw Bot API), as plain dicts - aiogram
accepts them via `InlineKeyboardMarkup.model_validate(...)`.

callback_data is capped at 64 bytes by Telegram; list ids are 32 hex chars,
so "lt:<id>:<index>" fits comfortably.
"""

import html
from typing import Optional

from app.core.config import settings
from app.services.telegram_texts import bot_lang, format_price, t

# Item buttons show "☐ name — price store"; Telegram truncates long button
# text visually anyway, but a hard cap keeps the cheapest price visible.
MAX_BUTTON_NAME = 34


def site_list_url(list_id: str, lang: Optional[str]) -> str:
    return f"{settings.frontend_url.rstrip('/')}/{bot_lang(lang)}/list/{list_id}"


def site_url_usable() -> bool:
    """Telegram rejects the whole message (BUTTON_URL_INVALID) if a URL
    button points at localhost - true in local dev, where buttons to the
    site are simply left out."""
    url = settings.frontend_url.lower()
    return not any(host in url for host in ("://localhost", "://127.0.0.1"))


def _short(name: str, limit: int = MAX_BUTTON_NAME) -> str:
    return name if len(name) <= limit else name[: limit - 1].rstrip() + "…"


def list_message_text(resolved: dict, lang: Optional[str]) -> str:
    items = resolved["items"]
    name = html.escape(resolved.get("name") or t(lang, "list_untitled"))
    done = sum(1 for i in items if i["checked"])
    lines = [t(lang, "list_header", name=name, done=done, n=len(items))]
    if not items:
        lines.append(t(lang, "list_empty"))
    elif resolved.get("total_cheapest"):
        lines.append(t(lang, "list_total", total=format_price(resolved["total_cheapest"], resolved["country"])))
    return "\n".join(lines)


def list_keyboard(resolved: dict, lang: Optional[str], *, role: Optional[str], join_url: Optional[str] = None) -> dict:
    """`role`: "owner" (share + invite buttons), "member" (leave button),
    "chat" (a message posted into some chat via inline mode: `join_url`
    lets people there open the list in the bot), anything else = plain."""
    rows = []
    for index, item in enumerate(resolved["items"]):
        mark = "☑️" if item["checked"] else "⬜"
        price = ""
        if not item["checked"] and item["min_price"] is not None:
            price = f" — {format_price(item['min_price'], resolved['country'])}"
            if item.get("cheapest_store") and len(resolved["stores"]) > 1:
                price += f" {item['cheapest_store']}"
        rows.append([{"text": f"{mark} {_short(item['name'])}{price}", "callback_data": f"lt:{resolved['id']}:{index}"}])

    if role == "owner":
        rows.append([
            {"text": t(lang, "btn_invite"), "callback_data": f"li:{resolved['id']}"},
            {"text": t(lang, "btn_share_list"), "switch_inline_query": f"list {resolved['id']}"},
        ])
    footer = []
    if role == "chat" and join_url:
        footer.append({"text": t(lang, "btn_open_in_bot"), "url": join_url})
    elif site_url_usable():
        footer.append({"text": t(lang, "btn_list_site"), "url": site_list_url(resolved["id"], lang)})
    if role == "member":
        footer.append({"text": t(lang, "btn_leave"), "callback_data": f"lx:{resolved['id']}"})
    if footer:
        rows.append(footer)
    return {"inline_keyboard": rows}
