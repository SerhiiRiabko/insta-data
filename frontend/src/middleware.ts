/**
 * Next.js Middleware for i18n routing
 * Redirects requests to appropriate locale
 */

import createMiddleware from 'next-intl/middleware';
import { locales, defaultLocale } from '@/i18n';

export default createMiddleware({
  locales,
  defaultLocale,
  localePrefix: 'always',
});

export const config = {
  matcher: [
    // Skip static files and internal Next.js routes
    '/((?!api|_next|_vercel|.*\\..*).*)',
  ],
};