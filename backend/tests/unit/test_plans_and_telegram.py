"""Plans, free-plan gating, Telegram account linking, lists and bot search.

Runs against a throwaway database on the local MongoDB (skipped if none is
reachable) - these features are mostly Mongo queries, so a real server
catches far more than mocks would.
"""

import uuid
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.database import mongodb

TEST_DB = "insta_data_test_plans"


@pytest_asyncio.fixture
async def db():
    client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=1500)
    try:
        await client.admin.command("ping")
    except Exception:
        pytest.skip("local MongoDB not reachable")
    await client.drop_database(TEST_DB)
    database = client[TEST_DB]
    mongodb._mongo_db = database
    await database.stores.insert_many([
        {"_id": "s1", "name": "АТБ", "initial": "А", "color": "#000", "country": "UA", "active": True, "url": ""},
        {"_id": "s2", "name": "Сільпо", "initial": "С", "color": "#111", "country": "UA", "active": True, "url": ""},
    ])
    from app.services import telegram_accounts
    await telegram_accounts.ensure_indexes()
    yield database
    await client.drop_database(TEST_DB)
    mongodb._mongo_db = None
    client.close()


async def _user(db, **fields):
    doc = {"_id": uuid.uuid4().hex, "email": None, "password_hash": None, "is_admin": False, "created_at": datetime.utcnow(), **fields}
    await db.users.insert_one(doc)
    return doc


# --- plans -------------------------------------------------------------------

async def test_effective_plan_prefers_gold_and_ignores_expired(db):
    from app.services.subscription_service import effective_plan, grant_plan

    user = await _user(db, email="a@example.com", compare_until=datetime.utcnow() - timedelta(days=1))
    assert effective_plan(user) == "free"
    user = await grant_plan(user["_id"], "compare", source="test")
    assert effective_plan(user) == "compare"
    user = await grant_plan(user["_id"], "gold", source="test")
    assert effective_plan(user) == "gold"
    assert effective_plan({"is_admin": True}) == "gold"
    assert effective_plan(None) == "free"


async def test_grant_extends_from_current_expiry(db):
    from app.services.subscription_service import grant_plan

    future = datetime.utcnow() + timedelta(days=10)
    user = await _user(db, gold_until=future)
    user = await grant_plan(user["_id"], "gold", source="test")
    assert abs((user["gold_until"] - (future + timedelta(days=30))).total_seconds()) < 5


async def test_stars_payment_is_idempotent_and_uses_telegram_expiry(db):
    from app.services.subscription_service import record_stars_payment, stars_invoice_payload

    user = await _user(db)
    expires = int((datetime.utcnow() + timedelta(days=30)).timestamp())
    kwargs = dict(charge_id="ch1", payload=stars_invoice_payload("compare", user["_id"]), stars=300,
                  payer_telegram_id=1, subscription_expiration_date=expires, is_recurring=False)
    first = await record_stars_payment(**kwargs)
    second = await record_stars_payment(**kwargs)
    assert first["compare_until"] == second["compare_until"] == datetime.utcfromtimestamp(expires)
    assert await db.payments.count_documents({}) == 1
    assert await record_stars_payment(**{**kwargs, "charge_id": "ch2", "payload": "garbage"}) is None


async def test_card_request_dedupes_and_approval_grants_once(db):
    from app.services.subscription_service import create_payment_request, decide_payment_request, effective_plan

    user = await _user(db)
    request, created = await create_payment_request(user["_id"], "gold", 10, "paid from Ivan")
    again, created_again = await create_payment_request(user["_id"], "gold", 10)
    assert created and not created_again and again["_id"] == request["_id"]

    assert (await decide_payment_request(request["_id"], True, "admin"))["status"] == "approved"
    assert await decide_payment_request(request["_id"], True, "admin") is None  # second click
    assert effective_plan(await db.users.find_one({"_id": user["_id"]})) == "gold"


async def test_pending_grant_applies_on_registration(db):
    from app.services.subscription_service import apply_pending_grants, effective_plan, queue_grant_for_email

    await queue_grant_for_email("New@Example.com", "gold", None)
    user = await _user(db, email="new@example.com")
    user = await apply_pending_grants(user)
    assert effective_plan(user) == "gold"
    assert await db.pending_grants.count_documents({}) == 0


# --- free-plan gating ----------------------------------------------------------

def test_gate_matrix_narrows_free_plan_to_one_store():
    from app.api.v1.endpoints.products import gate_matrix

    stores = [{"name": "A"}, {"name": "B"}]
    products = [
        {"id": "1", "prices": [1.0, 2.0], "promo": [False, True]},
        {"id": "2", "prices": [None, 3.0], "promo": [False, False]},
    ]
    free = gate_matrix(products, stores, None, "B")
    assert [p["prices"] for p in free["products"]] == [[2.0], [3.0]]
    assert free["products"][0]["promo"] == [True]
    assert free["stores"] == [{"name": "B"}]
    assert free["access"]["selected_store"] == "B" and not free["access"]["compare"]

    default_store = gate_matrix(products, stores, None, "nonexistent")
    assert [p["id"] for p in default_store["products"]] == ["1"]

    paid = gate_matrix(products, stores, {"is_admin": True}, None)
    assert paid["products"] == products and paid["stores"] == stores


# --- Telegram accounts -------------------------------------------------------------

async def test_telegram_only_users_coexist_and_merge_on_link(db):
    from app.services import telegram_accounts

    bot_user = await telegram_accounts.get_or_create_telegram_user({"id": 111, "username": "Petro", "language_code": "uk"})
    other_bot_user = await telegram_accounts.get_or_create_telegram_user({"id": 222, "username": None})
    assert bot_user["email"] is None and other_bot_user["email"] is None  # partial unique index allows both
    assert bot_user["bot_lang"] == "ukr"

    gold_until = datetime.utcnow() + timedelta(days=20)
    await db.users.update_one({"_id": bot_user["_id"]}, {"$set": {"gold_until": gold_until}})
    await db.shopping_lists.insert_one({"_id": "L1", "owner_user_id": bot_user["_id"], "items": []})

    site_user = await _user(db, email="petro@example.com", password_hash="x")
    linked = await telegram_accounts.link_telegram(site_user["_id"], {"id": 111, "username": "Petro"})
    assert linked["telegram_id"] == 111 and linked["telegram_username_lc"] == "petro"
    assert abs((linked["gold_until"] - gold_until).total_seconds()) < 0.01  # Mongo stores milliseconds
    assert await db.users.find_one({"_id": bot_user["_id"]}) is None
    assert (await db.shopping_lists.find_one({"_id": "L1"}))["owner_user_id"] == site_user["_id"]

    another_site_user = await _user(db, email="other@example.com")
    with pytest.raises(telegram_accounts.LinkError) as err:
        await telegram_accounts.link_telegram(another_site_user["_id"], {"id": 111})
    assert err.value.code == "telegram_linked_elsewhere"

    assert (await telegram_accounts.find_user_by_identifier("@PETRO"))["_id"] == site_user["_id"]
    assert (await telegram_accounts.find_user_by_identifier("111"))["_id"] == site_user["_id"]
    assert (await telegram_accounts.find_user_by_identifier("Petro@Example.com"))["_id"] == site_user["_id"]


async def test_login_token_is_single_use(db):
    from app.services import telegram_accounts

    token = await telegram_accounts.create_token("login")
    assert await telegram_accounts.consume_token(token, "login", from_status="confirmed") is None  # not confirmed yet
    assert await telegram_accounts.confirm_token(token, "login", user_id="u1")
    assert await telegram_accounts.confirm_token(token, "login", user_id="attacker") is None
    assert (await telegram_accounts.consume_token(token, "login", from_status="confirmed"))["user_id"] == "u1"
    assert await telegram_accounts.consume_token(token, "login", from_status="confirmed") is None


# --- lists + search -------------------------------------------------------------------

async def _seed_products(db):
    await db.products.insert_many([
        {"id": "p1", "country": "UA", "name": "Молоко Галичина 2,5%", "unit": "900 г",
         "prices": [42.9, 45.0], "promo": [False, True], "name_i18n": {"eng": "Milk Halychyna 2.5%", "mne": "Mlijeko Halychyna 2,5%"}},
        {"id": "p2", "country": "UA", "name": "Шоколад молочний Roshen", "unit": "90 г", "prices": [None, 39.0], "promo": [False, False]},
        {"id": "p3", "country": "UA", "name": "Хліб білий", "unit": "", "prices": [20.0, None], "promo": [False, False]},
    ])


async def test_list_resolves_country_stores_translation_and_total(db):
    from app.services import list_service

    await _seed_products(db)
    doc = await list_service.create_list(None, [{"product_id": "p1", "name": "Молоко"}, {"product_id": "p3", "name": "Хліб"}], "UA")
    resolved = await list_service.resolve_list(doc, "eng")
    assert [s["name"] for s in resolved["stores"]] == ["АТБ", "Сільпо"]
    assert resolved["items"][0]["name"] == "Milk Halychyna 2.5%"
    assert resolved["items"][0]["cheapest_store"] == "АТБ"
    assert resolved["total_cheapest"] == 62.9

    doc = await list_service.toggle_item(doc["_id"], index=1)
    assert (await list_service.resolve_list(doc, "srb"))["items"][0]["name"] == "Mlijeko Halychyna 2,5%"  # srb -> mne
    assert (await list_service.resolve_list(doc, "ukr"))["total_cheapest"] == 42.9


async def test_legacy_list_without_country_is_inferred(db):
    from app.services import list_service

    await _seed_products(db)
    now = datetime.utcnow()
    await db.shopping_lists.insert_one({"_id": "old", "items": [{"product_id": "p3", "name": "Хліб", "checked": False}],
                                        "owner_user_id": None, "created_at": now, "updated_at": now})
    resolved = await list_service.resolve_list(await list_service.get_list_doc("old"), "ukr")
    assert resolved["country"] == "UA"
    assert (await db.shopping_lists.find_one({"_id": "old"}))["country"] == "UA"


async def test_bot_search_ranks_exact_word_first_and_matches_translations(db):
    from app.services.product_query import in_store, search_country, store_counts

    await _seed_products(db)
    docs = await search_country("молоко", "UA", "ukr")
    assert [d["id"] for d in docs] == ["p1"]  # "молочний" doesn't contain "молоко"
    docs = await search_country("молоч", "UA", "ukr")
    assert [d["id"] for d in docs] == ["p2"]
    docs = await search_country("milk", "UA", "eng")
    assert [d["id"] for d in docs] == ["p1"]
    docs = await search_country("мол", "UA", "ukr")
    assert store_counts(docs, 2) == [1, 2]
    assert [d["id"] for d, _ in in_store(docs, 0)] == ["p1"]
    assert await search_country("a", "UA", "ukr") == []  # too short
    assert await search_country(".*", "UA", "ukr") == []  # regex metacharacters are escaped
