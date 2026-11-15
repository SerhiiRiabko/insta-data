"""Bot entry point: `python -m bot.main` (from backend/, same venv and .env
as the API). Long polling - the server has no domain/HTTPS for a webhook."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

from app.core.config import settings
from app.database.mongodb import close_mongo_db, init_mongo_db
from app.services import list_service, telegram_accounts
from bot.handlers import UserMiddleware, router

logger = logging.getLogger("bot")

COMMANDS = {
    None: [
        ("plan", "Plan and payment"), ("lists", "Shopping lists"), ("country", "Country"),
        ("lang", "Language"), ("site", "Log in to the website"), ("help", "Help"), ("paysupport", "Payment support"),
    ],
    "uk": [
        ("plan", "Тариф і оплата"), ("lists", "Списки покупок"), ("country", "Країна"),
        ("lang", "Мова"), ("site", "Увійти на сайт"), ("help", "Допомога"), ("paysupport", "Питання щодо оплати"),
    ],
    "ru": [
        ("plan", "Тариф и оплата"), ("lists", "Списки покупок"), ("country", "Страна"),
        ("lang", "Язык"), ("site", "Войти на сайт"), ("help", "Помощь"), ("paysupport", "Вопросы по оплате"),
    ],
    "sr": [
        ("plan", "Paket i plaćanje"), ("lists", "Liste za kupovinu"), ("country", "Zemlja"),
        ("lang", "Jezik"), ("site", "Prijava na sajt"), ("help", "Pomoć"), ("paysupport", "Pitanja o plaćanju"),
    ],
}


async def main() -> None:
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")

    await init_mongo_db()
    await telegram_accounts.ensure_indexes()
    await list_service.ensure_indexes()
    from app.database.mongodb import get_mongo_db
    await get_mongo_db().bot_searches.create_index("created_at", expireAfterSeconds=24 * 3600, name="ttl_created_at")

    bot = Bot(settings.telegram_bot_token, default=DefaultBotProperties(parse_mode="HTML", link_preview_is_disabled=True))
    for language, commands in COMMANDS.items():
        await bot.set_my_commands(
            [BotCommand(command=c, description=d) for c, d in commands],
            scope=BotCommandScopeAllPrivateChats(),
            language_code=language,
        )

    dp = Dispatcher()
    middleware = UserMiddleware()
    dp.message.outer_middleware(middleware)
    dp.callback_query.outer_middleware(middleware)
    dp.inline_query.outer_middleware(middleware)
    dp.pre_checkout_query.outer_middleware(middleware)
    dp.include_router(router)

    me = await bot.get_me()
    logger.info(f"Starting @{me.username}")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await close_mongo_db()


if __name__ == "__main__":
    asyncio.run(main())
