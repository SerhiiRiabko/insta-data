/**
 * API Client
 * Axios instance with base configuration
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type { Lang } from './productMatrix';

export type Country = 'ME' | 'UA';

export type Plan = 'free' | 'compare' | 'gold';

/** What the current user may see - returned by /auth/me and every matrix endpoint. */
export interface Access {
  plan: Plan;
  compare: boolean;
  lists: boolean;
  expires_at: string | null;
  forever: boolean;
  // Matrix endpoints only: the store picker for the free plan.
  all_stores?: { name: string; initial: string; color: string }[];
  selected_store?: string | null;
}

export interface CurrentUser {
  id: string;
  email: string | null;
  is_admin: boolean;
  has_password: boolean;
  telegram: { id: number; username: string | null; first_name: string | null } | null;
  access: Access;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export const TELEGRAM_BOT_USERNAME = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME || 'helperinshopping_bot';

export const telegramBotLink = (startPayload?: string) =>
  `https://t.me/${TELEGRAM_BOT_USERNAME}${startPayload ? `?start=${startPayload}` : ''}`;

const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  // Send/receive the auth session cookie (Phase 4.2) - cookies are
  // host-scoped, not port-scoped, so this works across localhost:3001 (this
  // app) <-> localhost:8001 (the API) as long as the backend's CORS
  // allow_origins lists this exact origin (it does, see core/config.py).
  withCredentials: true,
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      console.error('Unauthorized access');
    }
    return Promise.reject(error);
  }
);

export default api;

/**
 * Products API functions (Frontend Integration)
 */
// `store`: on the free plan the backend returns only this one store's
// prices (see gate_matrix in backend/app/api/v1/endpoints/products.py);
// paid plans ignore it and get every store.
export const productsAPI = {
  priceMatrix: (lang: Lang = 'ukr', country: Country = 'ME', store?: string | null) =>
    api.get('/products/matrix', { params: { lang, country, store: store || undefined } }),

  // Fast default for page load: last persisted scan from MongoDB, refreshed
  // automatically once a week (Mon 07:00 Kyiv) by the backend scheduler.
  // Phase 4.6: `lang` resolves each product's translated name server-side
  // (falls back to the source name when no translation is cached yet).
  matrixCached: (lang: Lang = 'ukr', country: Country = 'ME', store?: string | null) =>
    api.get('/products/matrix-cached', { params: { lang, country, store: store || undefined } }),

  // Manual "Оновити ціни" trigger + the weekly scheduled job on the backend
  // both hit a real scrape: cijene.me's JSON API for ME (~10-15s), but the
  // UA pipeline (АТБ/Сільпо/Varus) drives real Playwright browsers across
  // ~10 categories per store with no shared aggregator, which is much
  // slower (~90-120s) - timeout sized for the slower of the two so a UA
  // refresh doesn't get cut off client-side while the scrape (and its
  // background persist) keeps running server-side regardless.
  priceMatrixLive: (lang: Lang = 'ukr', country: Country = 'ME', store?: string | null) =>
    api.get('/products/matrix-live', { params: { lang, country, store: store || undefined }, timeout: 150000 }),

  // Same live scrape as priceMatrixLive, grouped into product-group
  // categories (Овочі, Фрукти, Молочка, Бакалія...) instead of a flat list.
  byCategory: (lang: Lang = 'ukr', country: Country = 'ME') =>
    api.get('/products/by-category', { params: { lang, country }, timeout: 150000 }),

  list: (limit: number = 50, skip: number = 0, lang: Lang = 'ukr') =>
    api.get('/products/list', { params: { limit, skip, lang } }),
};

/**
 * Countries API — backs the country selector (site header + admin store form).
 */
export const countriesAPI = {
  list: () => api.get('/countries'),
};

/**
 * Shopping lists API (Phase 4.1 — guest mode: create once, then view/toggle
 * via the list id, which is also the shareable link).
 */
export interface ShoppingListItemInput {
  product_id: string;
  name: string;
  unit: string;
}

// Creating/saving/editing a list and sending it to Telegram need the Gold
// plan (403 `gold_required`); viewing and ticking items stay open to anyone
// with the link.
export const listsAPI = {
  create: (items: ShoppingListItemInput[], sessionId: string | null, country: Country, lang: Lang) =>
    api.post('/lists', { items, session_id: sessionId, country }, { params: { lang } }),

  get: (listId: string, lang: Lang) => api.get(`/lists/${listId}`, { params: { lang } }),

  toggleItem: (listId: string, productId: string, lang: Lang) =>
    api.patch(`/lists/${listId}/toggle`, { product_id: productId }, { params: { lang } }),

  addItem: (listId: string, item: ShoppingListItemInput) =>
    api.post(`/lists/${listId}/items`, item),

  removeItem: (listId: string, productId: string) =>
    api.delete(`/lists/${listId}/items/${productId}`),

  // Phase 4.2 — requires an active session cookie (see authAPI below)
  mine: () => api.get('/lists/mine'),

  save: (listId: string, name: string, lang: Lang) =>
    api.post(`/lists/${listId}/save`, { name }, { params: { lang } }),

  sendTelegram: (listId: string, username: string, lang: Lang) =>
    api.post(`/lists/${listId}/send-telegram`, { username, lang }),
};

/**
 * Paid plans: Telegram Stars (needs a linked Telegram) or a card transfer
 * an admin approves.
 */
export const subscriptionsAPI = {
  plans: () => api.get('/subscriptions/plans'),
  me: () => api.get('/subscriptions/me'),
  starsInvoice: (plan: Plan, lang: Lang) => api.post('/subscriptions/stars-invoice', { plan, lang }),
  cardRequest: (plan: Plan, comment: string) => api.post('/subscriptions/card-request', { plan, comment }),
};

/**
 * Auth API (Phase 4.2) — email+password or passwordless magic link, user's
 * choice. Either way the session lives in an HttpOnly cookie the browser
 * sends automatically (see `withCredentials` above); there's no token to
 * store in JS.
 */
export const authAPI = {
  register: (email: string, password: string) =>
    api.post('/auth/register', { email, password }),

  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),

  magicLinkRequest: (email: string, lang: string) =>
    api.post('/auth/magic-link/request', { email, lang }),

  me: () => api.get('/auth/me'),

  logout: () => api.post('/auth/logout'),

  // Telegram: the site opens the returned t.me deep link, the user confirms
  // in the bot, and the site polls the status endpoint.
  telegramLogin: (lang: Lang) => api.post('/auth/telegram/login', { lang }),
  telegramLoginStatus: (token: string) => api.get(`/auth/telegram/login/${token}`),
  telegramLink: (plan?: Plan) => api.post('/auth/telegram/link', { plan: plan ?? null }),
  telegramLinkStatus: (token: string) => api.get(`/auth/telegram/link/${token}`),
  telegramUnlink: () => api.delete('/auth/telegram'),

  // Adds email+password to an account that started in the bot.
  setCredentials: (email: string, password: string) => api.post('/auth/credentials', { email, password }),
};

/**
 * Stores API (Phase 4.3). GET is public (drives the "Магазини" page); the
 * rest requires an admin session (Phase 4.4).
 */
export interface StoreInput {
  name: string;
  initial: string;
  color: string;
  url: string;
  active: boolean;
  country: Country;
}

export const storesAPI = {
  list: (includeInactive = false, country?: Country) =>
    api.get('/stores', { params: { include_inactive: includeInactive, country } }),

  create: (store: StoreInput) => api.post('/stores', store),

  update: (id: string, store: StoreInput) => api.put(`/stores/${id}`, store),

  deactivate: (id: string) => api.delete(`/stores/${id}`),
};

/**
 * Scraper agents API (Phase 4.5) — admin visibility + manual trigger for the
 * scraping pipeline. All routes require an admin session.
 */
export interface ScraperAgentInput {
  name: string;
  strategy: 'cijene' | 'instagram' | 'custom';
  store_ids: string[];
  url: string | null;
  active: boolean;
}

export const scraperAgentsAPI = {
  list: () => api.get('/scraper-agents'),

  create: (agent: ScraperAgentInput) => api.post('/scraper-agents', agent),

  update: (id: string, agent: ScraperAgentInput) => api.put(`/scraper-agents/${id}`, agent),

  deactivate: (id: string) => api.delete(`/scraper-agents/${id}`),

  // cijene.me runs are near-instant (a JSON API call); the instagram mock is
  // instant too - no special timeout needed beyond the default.
  run: (id: string) => api.post(`/scraper-agents/${id}/run`),
};

/**
 * Admin API — plan prices & card details, users and their plans, card
 * transfer requests, catalog translation. All routes require `is_admin`.
 */
export interface PlanSettings {
  compare_stars: number;
  gold_stars: number;
  compare_eur: number;
  gold_eur: number;
  gold_list_limit: number;
  card_details: string;
}

export const adminAPI = {
  getPlanSettings: () => api.get('/admin/plan-settings'),

  updatePlanSettings: (settings: Partial<PlanSettings>) => api.put('/admin/plan-settings', settings),

  listUsers: (q?: string) => api.get('/admin/users', { params: { q: q || undefined } }),

  // identifier: email, @username or numeric Telegram id; months null = forever
  grant: (identifier: string, plan: Plan, months: number | null) =>
    api.post('/admin/users/grant', { identifier, plan, months }),

  revoke: (userId: string, plan: Plan | null) => api.post(`/admin/users/${userId}/revoke`, { plan }),

  paymentRequests: (status: 'pending' | 'all' = 'pending') =>
    api.get('/admin/payment-requests', { params: { status } }),

  decidePayment: (requestId: string, decision: 'approve' | 'decline') =>
    api.post(`/admin/payment-requests/${requestId}/${decision}`),

  translationStatus: () => api.get('/admin/translations/status'),

  fillTranslations: (country: Country) => api.post('/admin/translations/fill', null, { params: { country } }),
};

/**
 * Search API functions
 */
export const searchAPI = {
  products: (query: string, source?: string, limit?: number, lang?: Lang) =>
    api.get('/search/products', { params: { q: query, source, limit, lang } }),

  trending: (hours: number = 24, limit: number = 20) =>
    api.get('/search/trending', { params: { hours, limit } }),

  byPrice: (minPrice: number, maxPrice: number, source?: string) =>
    api.get('/search/price', { params: { min_price: minPrice, max_price: maxPrice, source } }),

  byStore: (store: string, limit?: number) =>
    api.get(`/search/cheapest/${store}`, { params: { limit } }),

  bySource: (source: string, limit?: number) =>
    api.get(`/search/source/${source}`, { params: { limit } }),

  stats: () => api.get('/search/stats'),
};

/**
 * Scraper API functions
 */
export const scraperAPI = {
  status: () => api.get('/scrapers/status'),

  runAll: () => api.post('/scrapers/run-all'),

  runSpecific: (store: string) => api.post('/scrapers/run', { store }),

  schedule: () => api.get('/scrapers/schedule'),

  pause: () => api.post('/scrapers/pause'),

  resume: () => api.post('/scrapers/resume'),

  logs: (store?: string, limit?: number) =>
    api.get('/scrapers/logs', { params: { store, limit } }),
};

/**
 * Instagram API functions
 */
export const instagramAPI = {
  scrape: (username: string, hoursBack?: number) =>
    api.post('/instagram/scrape', { username, hours_back: hoursBack || 48 }),

  testConnection: () => api.post('/instagram/test-connection'),

  status: () => api.get('/instagram/status'),
};