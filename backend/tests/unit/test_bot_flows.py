"""Bot conversation flows, driven through aiogram's real Dispatcher with a
recording fake session (no network): every Bot API call the handlers make
is captured, and outgoing raw-API calls (app.services.telegram_api) are
stubbed. Uses a throwaway database on the local MongoDB.
"""

import itertools
import uuid
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.methods import AnswerCallbackQuery, DeleteMessage, EditMessageText, GetMe, SendMessage
from aiogram.types import CallbackQuery, Chat, Message, Update, User
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.database import mongodb

TEST_DB = "insta_data_test_bot"
CHAT_ID = 555001
ADMIN_ID = 555002


class RecordingSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.calls = []
        self.ids = itertools.count(1000)

    async def make_request(self, bot, method, timeout=None):
        self.calls.append(method)
        if isinstance(method, GetMe):
            return User(id=1, is_bot=True, first_name="bot", username="helperinshopping_bot")
        if isinstance(method, SendMessage):
            return Message(message_id=next(self.ids), date=datetime.now(), chat=Chat(id=method.chat_id, type="private"), text=method.text)
        if isinstance(method, EditMessageText):
            return True
        return True

    async def close(self):
        pass

    async def stream_content(self, *args, **kwargs):  # pragma: no cover - not used
        raise NotImplementedError

    def of(self, kind):
        return [c for c in self.calls if isinstance(c, kind)]


@pytest_asyncio.fixture
async def env(monkeypatch):
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=1500)
    try:
        await client.admin.command("ping")
    except Exception:
        pytest.skip("local MongoDB not reachable")
    await client.drop_database(TEST_DB)
    db = client[TEST_DB]
    mongodb._mongo_db = db
    await db.stores.insert_many([
        {"_id": "s1", "name": "АТБ", "initial": "А", "color": "#000", "country": "UA", "active": True, "url": ""},
        {"_id": "s2", "name": "Сільпо", "initial": "С", "color": "#111", "country": "UA", "active": True, "url": ""},
    ])
    await db.products.insert_many([
        {"id": "p1", "country": "UA", "name": "Молоко Галичина 2,5%", "unit": "900 г", "prices": [42.9, 45.0], "promo": [False, True]},
        {"id": "p2", "country": "UA", "name": "Молоко Яготинське 3,2%", "unit": "870 г", "prices": [None, 51.0], "promo": [False, False]},
    ])

    raw_calls = []

    async def fake_call(method, **params):
        raw_calls.append((method, params))
        if method == "createInvoiceLink":
            return "https://t.me/$fakeinvoice"
        if method == "sendMessage":
            return {"message_id": 1}
        return True

    from app.services import telegram_api
    monkeypatch.setattr(telegram_api, "call", fake_call)
    monkeypatch.setattr(settings, "admin_telegram_usernames", "boss_admin")

    from app.services import telegram_accounts
    await telegram_accounts.ensure_indexes()

    from bot.handlers import UserMiddleware, router
    dp = Dispatcher()
    middleware = UserMiddleware()
    for observer in (dp.message, dp.callback_query, dp.inline_query, dp.pre_checkout_query):
        observer.outer_middleware(middleware)
    dp.include_router(router)
    session = RecordingSession()
    bot = Bot("42:TEST", session=session)

    yield {"db": db, "dp": dp, "bot": bot, "session": session, "raw": raw_calls}

    # The router is a module-level singleton; detach it so the next test's
    # Dispatcher can include it again.
    router._parent_router = None
    await client.drop_database(TEST_DB)
    mongodb._mongo_db = None
    client.close()


_update_ids = itertools.count(1)


def _user(uid=CHAT_ID, username="shopper"):
    return User(id=uid, is_bot=False, first_name="Test", username=username, language_code="uk")


async def say(env, text, uid=CHAT_ID, username="shopper"):
    message = Message(message_id=next(_update_ids), date=datetime.now(), chat=Chat(id=uid, type="private"), from_user=_user(uid, username), text=text)
    await env["dp"].feed_update(env["bot"], Update(update_id=next(_update_ids), message=message))


async def press(env, data, message_id, uid=CHAT_ID, username="shopper"):
    message = Message(message_id=message_id, date=datetime.now(), chat=Chat(id=uid, type="private"), text="…")
    callback = CallbackQuery(id=str(next(_update_ids)), from_user=_user(uid, username), chat_instance="ci", data=data, message=message)
    await env["dp"].feed_update(env["bot"], Update(update_id=next(_update_ids), callback_query=callback))


def buttons(method):
    markup = method.reply_markup
    return [b for row in markup.inline_keyboard for b in row] if markup else []


async def test_free_user_sees_one_store_at_a_time(env):
    session = env["session"]
    await say(env, "/start")
    assert "Привіт" in session.of(SendMessage)[0].text
    assert any(b.callback_data == "c:UA" for b in buttons(session.of(SendMessage)[1]))

    await say(env, "молоко")  # no country yet -> asks again, remembers the query
    await press(env, "c:UA", message_id=1)
    choice = session.of(SendMessage)[-1]
    store_buttons = [b for b in buttons(choice) if b.callback_data and b.callback_data.startswith("ss:")]
    assert [b.text for b in store_buttons] == ["АТБ · 1", "Сільпо · 2"]
    assert any(b.callback_data == "plan" for b in buttons(choice))

    first_choice_id = 1000 + len(session.of(SendMessage)) - 1
    await press(env, store_buttons[1].callback_data, message_id=first_choice_id)
    answer = session.of(EditMessageText)[-1]
    assert "Сільпо" in answer.text and "45,00 ₴" in answer.text and "51,00 ₴" in answer.text and "42,90" not in answer.text
    assert answer.reply_markup is None  # the store buttons are gone

    await say(env, "молоко")
    second_choice = session.of(SendMessage)[-1]
    second_choice_id = 1000 + len(session.of(SendMessage)) - 1
    atb = next(b for b in buttons(second_choice) if b.text.startswith("АТБ"))
    await press(env, atb.callback_data, message_id=second_choice_id)
    assert any(d.message_id == first_choice_id for d in session.of(DeleteMessage)), "previous store answer is deleted"
    assert "42,90 ₴" in session.of(EditMessageText)[-1].text


async def test_paid_users_compare_and_gold_adds_to_list(env):
    db, session = env["db"], env["session"]
    await say(env, "/start")
    await db.users.update_one({"telegram_id": CHAT_ID}, {"$set": {"country": "UA", "compare_until": datetime.utcnow() + timedelta(days=5)}})

    await say(env, "молоко")
    compare = session.of(SendMessage)[-1]
    assert "порівняння" in compare.text and "✅ АТБ 42,90 ₴" in compare.text and "Сільпо 45,00 ₴ 🏷" in compare.text
    assert compare.reply_markup is None  # compare plan has no list buttons

    await db.users.update_one({"telegram_id": CHAT_ID}, {"$set": {"gold_until": datetime.utcnow() + timedelta(days=5)}})
    await say(env, "молоко")
    gold = session.of(SendMessage)[-1]
    add = [b for b in buttons(gold) if b.callback_data.startswith("sa:")]
    assert [b.text for b in add] == ["➕1", "➕2"]
    await press(env, add[0].callback_data, message_id=1)
    assert "Додано" in session.of(AnswerCallbackQuery)[-1].text
    await press(env, add[0].callback_data, message_id=1)
    assert "уже є у списку" in session.of(AnswerCallbackQuery)[-1].text

    await say(env, "/lists")
    lists = session.of(SendMessage)[-1]
    await press(env, buttons(lists)[0].callback_data, message_id=1)
    shown = session.of(SendMessage)[-1]
    toggle = next(b for b in buttons(shown) if b.callback_data and b.callback_data.startswith("lt:"))
    assert toggle.text.startswith("⬜ Молоко Галичина")
    assert any(b.switch_inline_query for b in buttons(shown)), "owner gets the share button"
    await press(env, toggle.callback_data, message_id=1)
    assert "куплено 1/1" in session.of(EditMessageText)[-1].text


async def test_stars_offer_and_admin_approves_site_card_request(env):
    db, session, raw = env["db"], env["session"], env["raw"]
    await db.settings.insert_one({"_id": "plan_settings", "card_details": "UA00 0000"})
    await say(env, "/start")
    await say(env, "/start", uid=ADMIN_ID, username="boss_admin")

    await say(env, "/plan")
    plans = session.of(SendMessage)[-1]
    assert "Безкоштовний" in plans.text
    # Stars only in the bot (Telegram's digital-goods rule), even with card details set.
    assert {b.callback_data for b in buttons(plans)} == {"buy:compare", "buy:gold"}

    await press(env, "buy:gold", message_id=1)
    assert any(m == "createInvoiceLink" and p["subscription_period"] == 30 * 24 * 3600 and p["prices"][0]["amount"] == 900 for m, p in raw)
    assert buttons(session.of(SendMessage)[-1])[0].url == "https://t.me/$fakeinvoice"

    # A card transfer requested on the website reaches the admin in the bot.
    from app.services.payment_notifications import notify_admins_new_request
    from app.services.subscription_service import create_payment_request
    payer = await db.users.find_one({"telegram_id": CHAT_ID})
    request, _ = await create_payment_request(payer["_id"], "gold", 10, "from the website")
    await notify_admins_new_request(request)
    admin_notice = next(p for m, p in raw if m == "sendMessage" and p["chat_id"] == ADMIN_ID)
    assert "Запит на оплату" in admin_notice["text"]

    await press(env, f"pr:a:{request['_id']}", message_id=1, uid=CHAT_ID)  # not an admin
    assert (await db.payment_requests.find_one({}))["status"] == "pending"
    await press(env, f"pr:a:{request['_id']}", message_id=1, uid=ADMIN_ID, username="boss_admin")
    assert (await db.payment_requests.find_one({}))["status"] == "approved"
    payer = await db.users.find_one({"telegram_id": CHAT_ID})
    assert payer["gold_until"] > datetime.utcnow() + timedelta(days=29)
    assert any(m == "sendMessage" and p["chat_id"] == CHAT_ID and "підтверджено" in p["text"] for m, p in raw)


async def test_admin_grant_command_and_link_confirmation(env):
    db, session = env["db"], env["session"]
    await say(env, "/start")
    await say(env, "/start", uid=ADMIN_ID, username="boss_admin")

    await say(env, "/grant @shopper compare 3")  # from a non-admin: ignored
    assert (await db.users.find_one({"telegram_id": CHAT_ID})).get("compare_until") is None
    await say(env, "/grant @shopper compare 3", uid=ADMIN_ID, username="boss_admin")
    granted = (await db.users.find_one({"telegram_id": CHAT_ID}))["compare_until"]
    assert granted > datetime.utcnow() + timedelta(days=89)

    # Website "connect Telegram": the deep link must be confirmed explicitly.
    from app.services import telegram_accounts
    site_user = {"_id": uuid.uuid4().hex, "email": "site@example.com", "password_hash": "x", "is_admin": False, "created_at": datetime.utcnow()}
    await db.users.insert_one(site_user)
    token = await telegram_accounts.create_token("link", user_id=site_user["_id"], plan=None)
    await say(env, f"/start link_{token}")
    confirm = session.of(SendMessage)[-1]
    assert "site@example.com" in confirm.text
    await press(env, f"lk:{token}:y", message_id=1)
    linked = await db.users.find_one({"_id": site_user["_id"]})
    assert linked["telegram_id"] == CHAT_ID and linked["compare_until"] == granted  # paid days survive the merge
    assert await db.users.count_documents({"telegram_id": CHAT_ID}) == 1
    assert (await db.telegram_tokens.find_one({"_id": token}))["status"] == "linked"
