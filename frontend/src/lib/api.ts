/**
 * API Client
 * Axios instance with base configuration
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type { Lang } from './productMatrix';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

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
export const productsAPI = {
  priceMatrix: (lang: Lang = 'ukr') =>
    api.get('/products/matrix', { params: { lang } }),

  // Fast default for page load: last persisted scan from MongoDB, refreshed
  // automatically once a week (Mon 07:00 Kyiv) by the backend scheduler.
  // Phase 4.6: `lang` resolves each product's translated name server-side
  // (falls back to the source name when no translation is cached yet).
  matrixCached: (lang: Lang = 'ukr') =>
    api.get('/products/matrix-cached', { params: { lang } }),

  // Manual "Оновити ціни" trigger + the weekly scheduled job on the backend
  // both hit the real cijene.me scrape (~10-15s), hence the longer timeout.
  priceMatrixLive: (lang: Lang = 'ukr') =>
    api.get('/products/matrix-live', { params: { lang }, timeout: 30000 }),

  // Same live scrape as priceMatrixLive, grouped into product-group
  // categories (Овочі, Фрукти, Молочка, Бакалія...) instead of a flat list.
  byCategory: (lang: Lang = 'ukr') =>
    api.get('/products/by-category', { params: { lang }, timeout: 30000 }),

  list: (limit: number = 50, skip: number = 0, lang: Lang = 'ukr') =>
    api.get('/products/list', { params: { limit, skip, lang } }),
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

export const listsAPI = {
  create: (items: ShoppingListItemInput[], sessionId: string | null) =>
    api.post('/lists', { items, session_id: sessionId }),

  get: (listId: string) => api.get(`/lists/${listId}`),

  toggleItem: (listId: string, productId: string) =>
    api.patch(`/lists/${listId}/toggle`, { product_id: productId }),

  addItem: (listId: string, item: ShoppingListItemInput) =>
    api.post(`/lists/${listId}/items`, item),

  removeItem: (listId: string, productId: string) =>
    api.delete(`/lists/${listId}/items/${productId}`),

  // Phase 4.2 — requires an active session cookie (see authAPI below)
  mine: () => api.get('/lists/mine'),

  save: (listId: string, name: string) =>
    api.post(`/lists/${listId}/save`, { name }),
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
}

export const storesAPI = {
  list: (includeInactive = false) =>
    api.get('/stores', { params: { include_inactive: includeInactive } }),

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
 * Admin API (Phase 4.4) — tier limits + per-user tier assignment. All
 * routes require `is_admin` on the session (see authAPI.me()).
 */
export const adminAPI = {
  getTiers: () => api.get('/admin/tiers'),

  updateTiers: (limits: { free: number; simple: number; pro: number }) =>
    api.put('/admin/tiers', limits),

  listUsers: () => api.get('/admin/users'),

  setUserTier: (userId: string, tier: string) =>
    api.put(`/admin/users/${userId}/tier`, { tier }),
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