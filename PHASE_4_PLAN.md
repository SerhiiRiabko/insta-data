# Phase 4 — Accounts, Shopping Lists, Admin & Localization

Status: **Phase 4.0-4.6 all done.** This document captures the raw
feature request from the user (2026-07-13) verbatim-in-spirit, split into
buildable phases, plus what has actually shipped so far. Update the "Status"
line of each phase as work lands — do not delete history, append to it
(same convention as PROJECT_MAP.md / CLAUDE.md).

## Why this document exists

The request bundles ~10 features spanning UI polish, user accounts, shared/saved
shopping lists with tiered limits, an admin panel (content, stores, user tiers,
scraper agents), product translation, and 2 new locales. That's a genuine
multi-week backend+frontent effort with real architecture decisions (auth
strategy, where user/list data lives, admin auth). It's broken into phases so
each phase is independently shippable and reviewable, rather than one giant
uncontrolled change.

---

## Phase 4.0 — Quick UI wins ✅ DONE (2026-07-13)

No backend changes, no data model changes, low risk.

- **[Req #1] Search box visibility** — the hero search `<input>` had
  `border: none` and no explicit background. Once the Tailwind v4 pipeline was
  fixed (Phase "mobile landing" work, 2026-07-10), Tailwind's preflight reset
  the input's background to `transparent`, making it nearly invisible against
  the hero photo on desktop. Fixed in
  `frontend/src/components/LandingPageDesignBrief.tsx`: input now has
  `background-color: rgba(120, 130, 128, 0.3)` (gray, 30% opacity, per spec)
  and a visible `1px solid rgba(15, 20, 25, 0.25)` border.
- **[Req #2] Logo → home button** — the "M" logo + "Monte-Shop-Price" wordmark
  in the header is now a `<button onClick={onHomeClick}>`. `onHomeClick`
  (defined in `LandingPageDesignBrief()`) closes any open modal
  (Products/Stores/About) and smooth-scrolls to top. Since this is a
  single-page app (no real routing between sections — Products/Stores/About
  are modals over the same page), "go to the home page" = close modal + scroll
  top, not a route change.
- **[Req #10, partial] New locale files scaffolded** — `frontend/src/locales/`
  already had `mne.json` (Montenegrin), covering that part of the ask. Added
  `srb.json` (Serbian, ekavian: цена/cena) and `bos.json` (Bosnian, ijekavian:
  cijena, same pattern as Montenegrin). Wired into `frontend/src/i18n.ts` and
  `frontend/next-intl.config.ts` (`locales` array + `Locale` type + `pathnames`).
  All 5 routes (`/ukr /rus /mne /srb /bos`) verified 200 OK.
  **Not done yet**: these are next-intl message catalogs on the routing layer
  only. The actual landing page UI (`LandingPageDesignBrief.tsx`) has its own
  hardcoded `TRANSLATIONS` object with only `ru`/`uk`/`en` and a 3-button
  language switcher, completely disconnected from the next-intl locale system
  (pre-existing, previously-documented disconnect). Wiring the real UI switcher
  to show all 5 (or 6, see Req #9) languages, and making search/product data
  respect them, is **Phase 4.6** below — doing it now would mean redesigning
  the language switcher twice.

Verified via Playwright: overflow=0 at all breakpoints (unaffected), search
input computed style confirmed (`rgba(120,130,128,0.3)` bg / `1px` border),
logo click scrolls `scrollY` from 472→0, 0 console errors, `tsc --noEmit` clean.

---

## Phase 4.1 — Shopping Lists, guest mode (no login required) ✅ DONE (2026-07-13)

**[Req #3, guest flow]**

- Nav "Товари" renamed to "Список покупок"/"Список покупок"/"Shopping List"
  (ru/uk/en) in `LandingPageDesignBrief.tsx`. Clicking it opens
  `ShoppingListModal.tsx` (replaces the old `ProductsModal.tsx`, deleted —
  fully superseded): same search + lazy `/by-category` fetch as before, plus
  a "+ Add" button per product row that toggles it into a client-side cart.
- **Session identity + cart**: `frontend/src/lib/shoppingCart.ts` — a random
  UUID (`crypto.randomUUID()`) stored in `localStorage` (`monteShopSessionId`,
  sent as `owner_session_id` on create — not auth, just an anonymous-owner
  field Phase 4.2 will attach a real `owner_user_id` next to) and the cart
  itself (`monteShopCart`), so a page refresh before "Створити список" is
  pressed doesn't lose the in-progress selection.
- **"Створити список"** button, top-right of the modal header, shows a live
  count badge, disabled while the cart is empty. On click: `POST
  /api/v1/lists` with the cart items + session id, clears the local cart, and
  `router.push`es to `/[urlLocale]/list/[id]` (a new standalone Next.js route,
  not a modal) — the id is also the shareable link, matching the spec's
  build→create→view flow.
- **List view** (`ShoppingListView.tsx`, used by the new
  `app/[lang]/list/[id]/page.tsx` route): each item shows name/unit, a
  checkbox that strike-throughs the row on click (clicking again un-strikes
  it, per spec) and toggles it back, best price + cheapest store, and a
  4-store mini price strip (`—` for stores that don't carry it) — reuses
  `formatPrice`/`DEFAULT_STORES` from `lib/productMatrix.ts` rather than a
  third copy of that formatting logic. "Поділитися списком" (Share list)
  copies `window.location.href` to the clipboard.
- **Toggle persistence is server-side and shared**: clicking a checkbox
  `PATCH`es `/api/v1/lists/{id}/toggle`, which flips `checked` in MongoDB —
  verified with two separate browser contexts opening the same link: the
  second one sees the first one's toggle after a fresh load, exactly the
  "share with someone, they can also strike through while the session is
  alive" behavior from the spec.
- **Lifetime decision (made, not just flagged)**: 30-day inactivity TTL via a
  MongoDB TTL index on `updated_at` (`LIST_TTL_SECONDS` in `lists.py`) —
  chosen as a reasonable default for "exists during the session," revisit
  once Phase 4.2 lets a user "save" a list out from under this TTL.

**Backend**: new `backend/app/api/v1/endpoints/lists.py`, mounted at
`/api/v1/lists` in `router.py`. Collection `db.shopping_lists`: `_id` (uuid4
hex, doubles as the public list id), `items: [{product_id, name, unit,
checked}]`, `owner_session_id`, `owner_user_id` (`None` until Phase 4.2),
`created_at`, `updated_at`. Endpoints: `POST /lists` (create),
`GET /lists/{id}` (fetch, prices resolved live from `db.products` by id at
read time — so a list always shows current prices, not a stale snapshot),
`PATCH /lists/{id}/toggle`, `POST /lists/{id}/items`, `DELETE
/lists/{id}/items/{product_id}` (the last two aren't used by the guest flow
yet but are the same resource Phase 4.2's "edit a saved list" reuses).

**Verified end-to-end** (Playwright, both API-level via curl and full
browser flow): create → get → toggle → persistence across reload → a second
browser context opening the shared link sees the same checked state; 0
horizontal overflow on the new list page from 280px-1280px; 0 console errors;
`tsc --noEmit` clean. One real bug found and fixed during testing: `onClose()`
(unmounting the modal, and with it the `router` closure) was called *before*
`router.push(...)` in `createList()`, which sporadically dropped the
navigation to the new list page — fixed by pushing first, closing after.

---

## Phase 4.2 — Accounts (login) + saved/multiple lists + tiers ✅ DONE (2026-07-14)

**[Req #3, logged-in flow] + [Req #6, tier limits]**

- **Auth decision made**: both email+password AND passwordless magic link
  are implemented, user's choice at login time (per explicit follow-up
  request) - not an either/or. Session lives in an HttpOnly JWT cookie
  (`access_token`, `SameSite=Lax`, 30-day `session_expire_days`) either way;
  there's no token stored in JS.
  - `backend/app/services/auth_service.py` - `hash_password`/`verify_password`
    (passlib/bcrypt, pinned `bcrypt==4.0.1` because passlib 1.7.4 breaks on
    bcrypt's `__about__` removal in 4.1+), `create_session_token`/
    `decode_session_token` (python-jose), `get_current_user` (optional -
    returns `None` not a 401, so one dependency serves both guest and
    logged-in routes).
  - `backend/app/services/email_service.py` - magic-link email via the
    Resend Python SDK, **reusing the same `RESEND_API_KEY` already
    configured for MonteLand/KartIQ** (user's explicit go-ahead - "маємо
    змогу відправляти листи, як в інших проектах?"), sandbox sender
    `onboarding@resend.dev`. Dev fallback (no key / send throws): logs the
    link instead of sending, same pattern as the sibling projects.
  - `backend/app/api/v1/endpoints/auth.py` - `POST /auth/register`,
    `POST /auth/login`, `POST /auth/magic-link/request` (always returns the
    same generic message regardless of whether the email exists, to avoid
    account enumeration), `GET /auth/magic-link/verify?token=` (opened
    directly from the email in a real browser tab, so it's a
    `RedirectResponse` to `{FRONTEND_URL}/{lang}?authed=1` with the cookie
    set on the redirect itself - mutating an injected `Response` dependency
    has no effect once a *different* Response object is what's actually
    returned, a real bug caught during testing), `POST /auth/logout`,
    `GET /auth/me`.
  - `email-validator` added as a dependency - pydantic's `EmailStr` silently
    requires it at import time (`ImportError` on startup otherwise, hit and
    fixed during this session).
- **Frontend**: `frontend/src/components/AuthModal.tsx` - a tab toggle
  between "Magic Link" and "Пароль" (password, with login/register
  sub-toggle), rendered from a new 👤 avatar button in the header
  (`LandingPageDesignBrief.tsx` - shows the user's first initial once
  logged in, click to log out; `GET /auth/me` runs once on mount to restore
  a session across page loads). `frontend/src/lib/api.ts`'s axios instance
  now sets `withCredentials: true` - cookies are host-scoped, not
  port-scoped, so the session cookie set by `localhost:8001` is sent
  automatically by fetches from `localhost:3001` without any token plumbing.
- **Saved/multiple lists**: `ShoppingListModal.tsx` now takes a `currentUser`
  prop - if logged in, it fetches `GET /lists/mine` on open; with ≥1 saved
  list it shows a "Мої списки" panel first (name, item count, click to open)
  with "+ Новий список" to go to the builder, matching spec's "якщо нема
  списків — зразу як у незалогінених" (0 lists skips straight to the
  builder). `ShoppingListView.tsx` shows a "Зберегти список" button (name
  input + confirm, not a native `prompt()`) when logged in and the list
  isn't saved yet, calling `POST /lists/{id}/save`; already-saved lists show
  a "✓ Збережено" badge instead and the list's saved name replaces the
  generic "Список покупок" title.
- **Tier limits** (Free 3 / Simple 10 / Pro 100, `backend/app/core/tiers.py`,
  hardcoded for now - Phase 4.4 admin will make it configurable) enforced in
  `lists.py` both at create-time (if logged in when creating) and at
  save-time (a guest list being claimed also counts) via
  `_assert_under_tier_limit()`, returning 403 with a message the UI surfaces
  inline (both `ShoppingListModal`'s create button and `ShoppingListView`'s
  save form show the backend's error text, not just a silent console.error -
  a gap caught and fixed during this session).
- **Data model**: `shopping_lists` gained `name` (null until saved) and the
  already-present `owner_user_id` is now actually populated. The guest TTL
  index (`ttl_updated_at`, 30 days) was changed to a **partial index**
  (`partialFilterExpression={"owner_user_id": None}`) so saved lists are
  exempt - Mongo rejects re-creating an index of the same name with
  different options, so `_ensure_indexes()` catches that and does a
  drop-and-recreate once, self-healing from the Phase 4.1 index that didn't
  have the partial filter yet.

**Verified end-to-end, backend (curl) then full browser (Playwright)**:
register → me → duplicate-register (409) → wrong-password (401) → login;
create 3 lists while logged in (free tier) → 4th create → 403; magic-link
request → real Resend send confirmed (no error in logs) → token pulled
directly from Mongo (faster than waiting on an inbox) → `GET
.../verify?token=` redirects with `Set-Cookie` → reusing the same token →
400. In the browser: magic-link redirect lands with the session cookie set,
header avatar shows the right initial, "Список покупок" nav shows "Мої
списки" with all 3 saved lists, clicking one navigates to it and shows the
"Сохранено" badge (checked in the actual displayed language, Russian, per
the pre-existing `lang='ru'` default - not a bug), and attempting a 4th
create surfaces the tier-limit message inline without navigating away. 0
console errors, `tsc --noEmit` clean throughout.

---

## Phase 4.3 — Stores admin (content) + public Stores page ✅ DONE (2026-07-14)

**[Req #4]**

- New `backend/app/api/v1/endpoints/stores.py` / collection `db.stores`:
  `id, name, initial, color, url, active`. Seeded on first read from the
  same 4 stores that used to be hardcoded (`SEED_STORES`), so the app still
  works out of the box on a fresh database - same pattern as MOCK_STORES
  elsewhere. `GET /stores` is public; `POST`/`PUT`/`DELETE` (soft-delete via
  `active: false`, not a real delete - a scraper config or historic prices
  may still reference the id) require admin.
- **Deliberately did NOT touch the price-matrix scraping/matching pipeline**
  (`cijene_scraper.py`, `product_matcher.py`) - those still key off the
  store `name` string exactly as before. Migrating the *real* scraping
  engine onto this collection is real, separate, riskier work (touches
  fuzzy product matching across ~800 live products) that the actual request
  ("оновлювати списки магазинів, додавати сайти пошуку ціни") doesn't
  require yet - what's needed is that admin can maintain the store list
  shown to users and use it as the target when wiring up a new scraper in
  Phase 4.5, not that today's scraper already reads from Mongo.
- `frontend/src/components/StoresModal.tsx` - was fully hardcoded, now
  fetches `GET /api/v1/stores` on open (falls back to the same 4 stores if
  the request fails, so the public page never breaks).

---

## Phase 4.4 — Admin panel foundation (auth + user tiers + settings CMS) ✅ DONE (2026-07-14)

**[Req #6]** "Треба адмінка" — **decision made**: reuses the Phase 4.2 user
auth (not a separate login system) via an `is_admin: bool` flag on the user
document, gating `/[lang]/admin` in the *same* Next.js app (not a separate
tool - lowest effort, and everything it needs - session cookie, `authAPI` -
already exists).

- **The chicken-and-egg problem** (an admin-gated panel can't create the
  first admin) is solved by `backend/scripts/bootstrap_admin.py` - a
  one-time CLI (`python scripts/bootstrap_admin.py you@example.com`) that
  flips `is_admin` for a user who has already logged in once via the normal
  flow. Not exposed in the UI on purpose.
- `app/services/auth_service.py::require_admin` - hard auth (401 if not
  logged in, 403 if logged in but not admin) dependency, used by every
  admin-only route (`stores.py`'s write endpoints, all of `admin.py`).
- `backend/app/api/v1/endpoints/admin.py` - `GET/PUT /admin/tiers` (now
  backed by `db.settings` via `app/core/tiers.py::get_tier_limits()`/
  `set_tier_limits()`, hardcoded `DEFAULT_TIER_LIMITS` only as the
  fresh-database fallback - **[Req #6]'s "3/10/100" limits are no longer a
  deploy-time constant**), `GET /admin/users` + `PUT
  /admin/users/{id}/tier` (assign any user's tier).
- `frontend/src/app/[lang]/admin/` (`page.tsx` server wrapper +
  `AdminPageClient.tsx`) - unauthenticated visitors see the same
  `AuthModal` used everywhere else (magic link or password, their choice,
  consistent with Phase 4.2); logged-in non-admins see "Доступ заборонено";
  admins see 3 tabs: **Магазини** (the Phase 4.3 CRUD - add/edit/deactivate
  a store), **Тарифи** (edit the 3 tier limits), **Юзери** (list +
  per-user tier dropdown). Deliberately single-language (Ukrainian only,
  no `TRANSLATIONS` object) - it's an internal tool, not the public site,
  so the multi-language work doesn't apply here.

This is the *foundation* other admin-editable things attach to as they land
(Phase 4.5's scraper-agent tab, Phase 4.6's About-page content editor) -
each becomes a new tab + a new admin.py-style module, not a new tool.

**Verified end-to-end** (Playwright): unauthenticated `/admin` shows the
login modal; non-admin logged-in user gets 403 from the API and "Доступ
заборонено" in the UI; admin sees all 3 tabs; created a real store through
the Stores tab and confirmed it immediately appears via the public `GET
/stores` (then cleaned up); tier-limit edit persists and is picked up by
`/lists/mine`'s `limit` field for a real (non-admin) user in the same run
as the earlier Phase 4.2 verification. 0 real console errors (the two seen
were the expected 401 from the initial, pre-login `/auth/me` check - not
bugs), `tsc --noEmit` clean.

---

## Phase 4.5 — Scraper agents in admin ✅ DONE (2026-07-14)

**[Req #7]**

### Finding: two orchestrators exist, only one is real

Before building anything, investigation turned up that the backend has **two
separate scraper orchestrators**, not one:
- `app/services/scrapers/orchestrator.py` — the **active** one.
  `_register_scrapers()` hardcodes exactly two entries: `"cijene"` →
  `CijeneScraper()` (real cijene.me JSON API, covers Aroma/Voli/HDL/IDEA in a
  single scrape since cijene.me is a price-aggregator site, not per-store)
  and `"instagram"` → `InstagramMockScraper()` (fully mocked, no network).
  This is what `products.py`'s `_scrape_and_group_live()` — and therefore
  `/matrix-live`, `/by-category`, and the weekly `refresh_prices_job` —
  actually calls.
- `app/services/orchestrator.py` + `app/api/v1/endpoints/scrapers.py` — a
  more elaborate, unrelated legacy system (per-store `AromaScraper`/
  `VoliScraper`/etc. from `store_scrapers.py`, its own separate
  `AsyncIOScheduler` at a different cron than the real one, `pause`/`resume`
  endpoints matching the frontend's already-scaffolded
  `scraperAPI.pause()/.resume()`). It depends on `instagrapi` (pins pydantic
  1.x, conflicts with the rest of the pydantic-v2 stack) and is **already
  disabled** — `router.py` only mounts it inside a `try/except ImportError`
  with a comment calling it "legacy". Also found: a `ScraperLog` SQLAlchemy
  model (`app/database/models.py`) that's queried by the legacy router but
  **never written to anywhere** — dead persistence layer.

Decision: build Phase 4.5 on top of the **active** orchestrator only. Did not
touch, resurrect, or delete the legacy chain — flagging it here (as this
project's docs do with other found-dead-code, e.g. Phase 4.6's
`BRAND_PATTERNS`) rather than doing an unscoped cleanup pass.

### What was built

New Mongo collection `db.scraper_agents` (`app/api/v1/endpoints/
scraper_agents.py`, mounted at `/api/v1/scraper-agents`, all mutations
`require_admin`-gated same as Phase 4.3/4.4): `{id, name, strategy
("cijene"|"instagram"|"custom"), store_ids (FK list into db.stores, since
cijene.me alone produces prices for all 4 stores at once), url, active,
last_run_at, last_run_status, last_run_products_found, last_run_error}`.
Seeded on first load with two agents mirroring what the active orchestrator
already knows about — "Cijene.me" (strategy `cijene`, all 4 real stores) and
"Instagram (mock)" (strategy `instagram`) — store ids resolved from the
already-seeded `db.stores` (Phase 4.3).

- `GET /admin/scraper-agents` — list with last-run status.
- `POST /admin/scraper-agents` — add a new site: name/url/strategy/store_ids.
  Reuses the existing generic scraper for the known `cijene`/`instagram`
  strategies; a `custom` strategy is accepted (the config is saved) but
  **not runnable** — attempting to run one returns `400` with an explicit
  message that a genuinely new site layout needs a hand-written scraper
  class registered in `orchestrator.py`, exactly per this phase's stated
  scope limit (no auto-scraper-builder was invented).
- `PUT` / `DELETE` (soft-deactivate) — mirrors `stores.py`'s CRUD pattern.
- `POST /admin/scraper-agents/{id}/run` — for `cijene`/`instagram` agents,
  calls the real `ScraperOrchestrator().run_single(strategy)` and persists
  `last_run_status`/`last_run_at`/`last_run_products_found`/`last_run_error`
  from the actual result (not a stub).

Frontend: `scraperAgentsAPI` in `api.ts`; new "Скрейпери" tab in
`AdminPageClient.tsx` (4th tab, alongside Магазини/Тарифи/Юзери) — table of
agents with strategy/mapped-stores/last-run status, a "Запустити зараз"
button (disabled with a tooltip for non-runnable `custom` agents), and an
"+ Додати сайт" form (name, URL, strategy select, store checkboxes) with an
inline note explaining the `custom` strategy's runnability limit.

**Deliberately not built**: pause/resume for the real weekly
`refresh_prices_job` scheduler. The frontend's `scraperAPI.pause()/.resume()`
scaffolding (noticed during Phase 4.6's investigation) was already wired only
to the legacy, disabled scheduler chain, not the real one — Phase 4.5's
actual spec (list/trigger/add-a-site) doesn't ask for pause/resume, so this
stays flagged as pre-existing disconnected plumbing rather than being
extended or wired up.

**Verified end-to-end via curl first**, then via a real browser once
Playwright reconnected mid-session: unauthenticated `GET /scraper-agents` →
401; authenticated (real magic-link token pulled from `db.login_tokens`)
list triggers the seed and returns both agents with real resolved store ids;
ran the Instagram agent for real — `last_run_status` flipped to `success`,
`last_run_products_found: 15`, matching the mock scraper's actual output;
created a throwaway `custom`-strategy agent, confirmed running it returns
`400` with the expected message, then deactivated it (later fully deleted
from Mongo as test cleanup). `tsc --noEmit` clean; `/[lang]/admin` compiles
and serves 200 with no console/build errors in the Next.js log.

**Real-browser pass (Playwright)**: logged in as the real admin via a magic
link clicked through in an actual browser session, opened `/ukr/admin`, all
4 tabs render (Магазини/Скрейпери/Тарифи/Юзери); clicked "Скрейпери" and
confirmed the seeded agents + the earlier curl-tested Instagram run
(✓ Успішно · 15 товарів) render correctly; clicked "Запустити зараз" on the
**real** Cijene.me agent — this triggered an actual live scrape of the real
cijene.me site (not a mock) through the UI button, which returned
**✓ Успішно · 783 товарів**, updating the agent's status/timestamp in the UI
in real time. Zero console errors (only a harmless missing-favicon 404).

---

## Phase 4.6 — Localization: product translations, language-aware search, UI language reconciliation ✅ DONE (2026-07-14)

**[Req #8, #9, #10 remainder]**

### UI language reconciliation (the two-stack disconnect, finally fixed)

There were two independent i18n systems: next-intl URL routing
(`ukr|rus|mne|srb|bos`, scaffolded but not actually rendered — `app/[lang]/page.tsx`
ignored `params.lang` entirely) and a separate hardcoded `type Lang =
'ru'|'uk'|'en'` + `TRANSLATIONS` object driving the real 3-pill switcher in
`LandingPageDesignBrief.tsx`. Several components had their own hand-written
bridge functions translating between the two (`ListPageClient.tsx`:
`ukr→uk, rus→ru, else→ru`; `ShoppingListModal.tsx`: `ru→rus, uk→ukr, else→mne`
— note the silent, slightly-wrong `'en'→'mne'` fallback in the latter).

**Fix**: added a 6th locale (`eng`, matching the legacy system's `en` for
parity) to next-intl's config (`i18n.ts`, `next-intl.config.ts`,
`middleware.ts` picks it up automatically, new `locales/eng.json`), then made
the URL locale segment **the single source of truth** — `lib/productMatrix.ts`
now exports the canonical `type Lang = 'ukr'|'rus'|'mne'|'srb'|'bos'|'eng'`
(identical to the next-intl locale codes) plus `ALL_LANGS`, `LANG_LABEL`, and
`BCP47_TAG` (proper `<html lang>` tags — `mne`→`sr-ME`, `eng`→`en`, etc., since
the project's locale codes aren't valid BCP-47 on their own).

`LandingPageDesignBrief.tsx` no longer holds `lang` in local state seeded from
a hardcoded default — it reads the URL via `useParams()`, and the language
switcher (`setLang`) calls `router.push()` to swap the `[lang]` segment of the
current path, so changing language is a real navigation, not just a client
re-render. The old 3-pill switcher (`RU`/`UK`/`EN` buttons) became a native
`<select>` over `ALL_LANGS` — 6 pills would have reintroduced the horizontal
overflow Phase 4.0 fixed, especially combined with the logo/nav/avatar already
sharing the header row on mobile.

Every component that received `lang` as a prop (`StoresModal`, `AboutModal`,
`AuthModal`, `ShoppingListModal`, `ShoppingListView`, `PriceMatrixLanding`,
`PriceCardsMobile`) now imports the shared `Lang` type instead of
redeclaring `'ru'|'uk'|'en'` locally, and every hardcoded translation object in
those files was expanded from 3 to 6 locales (mne/srb/bos translations
written directly — South Slavic, close enough to hand-translate accurately;
eng added for parity). The two bridge functions in `ListPageClient.tsx` and
`ShoppingListModal.tsx` were deleted outright — `lang` **is** the URL locale
now, no mapping needed. `AdminPageClient.tsx`'s hardcoded `lang="uk"` (which
was already subtly wrong, "uk" isn't a locale in either system) became
`lang="ukr"`.

Verified: `tsc --noEmit` clean; all 6 locale routes (`/ukr`, `/rus`, `/mne`,
`/srb`, `/bos`, `/eng`) return 200 with real rendered content (checked via
curl, since the Playwright MCP tool was unavailable this session — see the
note under Verification below).

### Product translations (`name_i18n`)

New `backend/app/services/translation_service.py`:
- `SUPPORTED_LOCALES` (the 6 codes above) and `resolve_display_name(doc,
  locale)` — reads `doc["name_i18n"][locale]`, falls back to `doc["name"]`
  (the original scraped source name) if that locale hasn't been translated
  yet. This fallback is the documented, intentional behavior for untranslated
  products, not an error state.
- `extract_brand(name)` — splits a known brand token (`KNOWN_BRANDS`, extends
  the 5-entry `BRAND_PATTERNS` dict already in `product_matcher.py`, which
  turned out to be dead code — defined but never called anywhere) off the
  front/middle of a product name, so the AI prompt can be told to leave it
  untouched, per the explicit "manufacturer/brand name stays untranslated"
  requirement.
- `translate_name(name, target_locale)` / `translate_to_all_locales(name)` —
  calls the Groq chat-completions API (`settings.groq_api_key`,
  `settings.groq_model` = `llama-3.1-8b-instant`, both new in `config.py`,
  empty by default) with a brand-preserving prompt. **No LLM integration
  existed anywhere in this backend before this phase** (confirmed via a full
  grep — `resend_api_key` was the only `*_api_key` in `Settings`). Rather than
  silently reusing the Groq key already used for AI enrichment in the sibling
  `hrd-minion` project (a production Telegram bot with its own free-tier
  quota), this phase leaves `groq_api_key` empty by default and documents that
  it can be set later — reusing a *production bot's* API quota for a
  translate-on-demand feature in a different project is a bigger judgment call
  than the earlier Resend-key reuse (which the user explicitly invited) and
  wasn't asked for this time.
- Only `ukr`/`rus`/`eng` actually get machine-translated
  (`LOCALES_NEEDING_TRANSLATION`) — `mne`/`srb`/`bos` are close enough to the
  scraped source language (Montenegrin/Serbian, Latin script) that showing the
  untranslated source name is more accurate than risking a bad machine
  translation with no API key configured to verify against.

Two ways to populate `name_i18n`, both admin-gated (`require_admin`, same
Phase 4.2/4.4 session):
- **Manual**: `PUT /admin/products/{id}/translations` — admin types
  translations in directly, no AI required.
- **AI-assisted**: `POST /admin/products/{id}/translate` (one product) and
  `POST /admin/products/translate-missing?limit=20` (bulk, capped per call to
  bound cost/time) — both return an empty `name_i18n` (not an error) when no
  Groq key is configured, since that's the valid fallback state.

`products.py`'s five read endpoints (`/matrix`, `/matrix-cached`, `/list`,
`/matrix-live`, `/by-category`) all gained a `lang` query param
(`LANG_REGEX` built from `SUPPORTED_LOCALES`, default `"ukr"`) and resolve
names through `resolve_display_name()` — `format_product_row()` and
`_build_product_row()` both take `lang` now. Freshly-scraped groups
(`/matrix-live`, `/by-category`) have no `name_i18n` cache yet by definition,
so they naturally fall back to the canonical scraped name until the product
has gone through `/matrix-cached` and been translated. The frontend's
`productsAPI.*` calls in `api.ts` were updated to pass the active `Lang`
through on every call, and `LandingPageDesignBrief.tsx`'s price-matrix fetch
now re-runs whenever the URL locale changes (`useEffect(..., [fetchMatrix])`
with `fetchMatrix` depending on `lang`), so switching language actually
re-resolves product names, not just UI chrome text.

### Language-aware search [Req #9]

`SearchService.search()` gained a `lang` parameter. The existing `$text`
index only covers the source-language `name`/`description` fields (a single,
non-localized Mongo text index — confirmed in `product_service.py`), and
MongoDB doesn't allow `$text` inside `$or`, so a second pass was added
instead: if the `$text` search returns fewer than `limit` results and `lang`
is set, a case-insensitive regex query against `name_i18n.{lang}` runs and
the results are merged in, deduped by product id. `search.py`'s
`/search/products` endpoint threads `lang` through and resolves the response
names via `resolve_display_name()`. Products with no cached translation for
the active locale are still found (via the source-name `$text` match) — they
just display under their source name until translated, consistent with the
rest of this phase's fallback behavior.

### Verification

curl: `/products/matrix-cached?lang=eng` against the real (287-product)
database returns 200 with untranslated names falling back correctly;
`/products/matrix?lang=xx` (invalid locale) → 422 (regex-validated);
`/admin/products/translate-missing` and `/admin/products/{id}/translations`
→ 401 unauthenticated. Full authenticated round-trip: requested a real magic
link for the bootstrapped admin, pulled the token from `db.login_tokens`,
verified it for a session cookie, `PUT` a manual translation for a real
product, confirmed `/matrix-cached?lang=eng` returned the translated name
while `?lang=ukr` still correctly fell back to the source name for the same
product — then reverted the test translation. All 6 frontend locale routes
(`/ukr /rus /mne /srb /bos /eng`) return 200 with real rendered HTML (no
error page), confirmed via curl. `tsc --noEmit` clean on the frontend;
backend restarted clean with zero import errors from the new
`translation_service.py`/`admin.py`/`products.py`/`search.py` wiring.

**Not verified via real browser this session** — the Playwright MCP tool
disconnected partway through and wasn't available for this phase (unlike
Phases 4.0–4.4, which all got full browser verification). The curl-level
checks above cover every code path touched, but a real click-through of the
language switcher dropdown and a live search-box query in a non-default
locale haven't been eyeballed in an actual browser. Worth a follow-up pass
once Playwright is back.

### Follow-up (2026-07-17): dictionary translator + name_i18n actually populated

Phase 4.6 above shipped the *machinery* for `name_i18n` (fields, endpoints,
`resolve_display_name()` fallback) but nothing had ever populated it — the
only translator was the Groq AI path, gated on `groq_api_key`, which was
deliberately left empty (see above), so all 287 real products had
`name_i18n: {}` and every locale silently fell back to the raw scraped name.
Requirement: translate the *generic item word* per product (e.g. "Mlijeko
Imlek Moja kravica 2.8%" → "Молоко Imlek Moja kravica 2.8%" in `ukr`), never
the brand, to make search usable in the UI language.

**New `app/services/grocery_dictionary.py`** — a free, deterministic,
word-by-word translator built from the actual vocabulary in the 287-product
dataset (~150 entries: dairy, produce, meat/fish, beverages, snacks,
hygiene/household nouns + common adjectives like fresh/white/red/ground/sour).
`translate_via_dictionary(name, locale)` tokenizes the name, replaces only
tokens it recognises (diacritic- and case-insensitive lookup), and leaves
everything else — brand names, model numbers, percentages, regional variety
names — untouched. No API key, no network call, no risk of mistranslating a
brand. `translation_service.translate_name()` now tries this first and only
falls back to the Groq AI path (renamed `_translate_name_ai`) if the
dictionary matched nothing.

**Ingest-time hook**: `products.py::_persist_live_products` (the write path
every live cijene.me scrape goes through) now computes `name_i18n.{ukr,rus,eng}`
via the dictionary on every upsert, so newly-scraped products get translated
automatically — no admin click needed. **Backfill**: new one-off
`backend/scripts/backfill_translations.py` ran once against the existing 287
products — 281 (98%) got a real translation; the 6 that didn't (Coca Cola,
Red Bull, Munchmallow, Lino čokolino, Bananica Soko Štark, Smoki Flips Štark)
are pure brand/product-line names with no generic word to translate, which is
correct behavior, not a gap.

**Bug found and fixed along the way**: `SearchService.search()`'s `$text`
query threw on every call because the `products` collection had **no text
index at all** (`ensure_indexes()` was only ever wired into the old/unused
mock-scraper ingest path, never the real cijene.me one) — the broad
`except Exception` swallowed it and returned `[]` before the `name_i18n`
regex fallback ever got a chance to run, so `/search/products` silently
returned zero results for *any* query on real data, translated or not. Fixed
by creating the index (`main.py` startup, idempotent) and splitting the
`$text` try/except in `search_service.py` so a future index failure can't
take the `name_i18n` fallback down with it. Separately, `search.py`'s
`ProductSummary.source` was a required `str` while every live-scraped
product has `source: None` (cijene.me aggregates multiple stores per
product — there's no single source) — every real search request 500'd on
response validation until `source` was made `Optional[str]`.

**Verified end-to-end for real** (not just curl): `curl` against
`/products/matrix?lang=ukr|rus|eng` and `/search/products?q=молоко&lang=ukr`
(9 results, incl. "Кисле Молоко Drezga") / `?q=milk&lang=eng` (13 results) /
`?q=сир&lang=ukr` (19 results) confirmed real translated matches, not just
non-empty responses. Frontend verified in an actual Playwright browser
session at `localhost:3001/ukr`: the rendered price-matrix table shows
"Молоко 2.8% Lazine", "Йогурт Imlek Moja kravica sa 2.8% mm", "Буряк
Natureta", etc. — brand names intact, generic words translated, exactly the
requested behavior. No new console errors (only pre-existing/unrelated
404 favicon + expected 401 for an unauthenticated session).

---

## Sequencing note

Phases 4.1–4.2 (lists) and 4.3–4.5 (admin) are independent of each other and
could be reordered or parallelized. Phase 4.6 (i18n) touches both the product
data model and the UI language switcher, so it's easiest done last once the
admin panel (for product/store data entry) exists. Recommended default order
is as numbered above, but tell me if a different feature is more urgent and
I'll resequence.

**Phase 4.1 resolved**: session-identity = localStorage UUID, list TTL =
30 days (Mongo TTL index) - see Phase 4.1 above.
**Before starting Phase 4.2 or 4.4**, still need a decision on: auth strategy
(email+password vs magic link vs OAuth) and where admin auth lives.