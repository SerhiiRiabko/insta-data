/**
 * API Client
 * Axios instance with base configuration
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
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
  priceMatrix: (lang: 'ru' | 'uk' | 'en' = 'ru') =>
    api.get('/products/matrix', { params: { lang } }),

  // Phase 3: Live scraper data from all 5 sources (67 products)
  priceMatrixLive: () =>
    api.get('/products/matrix-live'),

  list: (limit: number = 50, skip: number = 0) =>
    api.get('/products/list', { params: { limit, skip } }),
};

/**
 * Search API functions
 */
export const searchAPI = {
  products: (query: string, source?: string, limit?: number) =>
    api.get('/search/products', { params: { q: query, source, limit } }),

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