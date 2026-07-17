/**
 * next-intl Configuration
 * Internationalization setup for multiple locales
 */

import { getRequestConfig } from 'next-intl/server';

export type Locale = 'ukr' | 'rus' | 'mne' | 'srb' | 'bos' | 'eng';

export const locales: Locale[] = ['ukr', 'rus', 'mne', 'srb', 'bos', 'eng'];
export const defaultLocale: Locale = 'ukr';

export const pathnames = {
  '/': '/',
  '/search': {
    ukr: '/search',
    rus: '/search',
    mne: '/search',
    srb: '/search',
    bos: '/search',
    eng: '/search',
  },
} as const;

export default getRequestConfig(async ({ locale }) => {
  if (!locales.includes(locale as Locale)) {
    return {};
  }

  try {
    const messages = (await import(`./src/locales/${locale}.json`)).default;
    return { messages };
  } catch (error) {
    console.error(`Failed to load messages for locale: ${locale}`);
    return {};
  }
});
