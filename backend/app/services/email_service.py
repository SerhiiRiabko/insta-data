"""Transactional email — magic-link login (Phase 4.2).

Same Resend pattern as MonteLand's `send_seller_welcome()` / KartIQ's
`send_confirmation_email()`: call the Resend API if a key is configured,
otherwise log the content (and the link, for magic links) so local dev
doesn't need a real inbox.
"""

import logging

import resend

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_magic_link_email(email: str, link: str) -> None:
    if not settings.resend_api_key:
        logger.info(f"[DEV] Magic link for {email}: {link}")
        return

    resend.api_key = settings.resend_api_key
    html = f"""
        <p>Натисніть, щоб увійти в Monte-Shop-Price:</p>
        <p><a href="{link}">{link}</a></p>
        <p style="color:#7d9a8d;font-size:13px">Посилання дійсне 15 хвилин. Якщо ви не запитували вхід — просто ігноруйте цей лист.</p>
    """
    try:
        resend.Emails.send({
            "from": f"{settings.email_from_name} <{settings.email_from}>",
            "to": [email],
            "subject": "Вхід у Monte-Shop-Price",
            "html": html,
        })
    except Exception as e:
        logger.error(f"Failed to send magic link email via Resend: {e}")
        logger.info(f"[FALLBACK] Magic link for {email}: {link}")