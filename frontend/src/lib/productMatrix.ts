/**
 * Shared price-matrix helpers used by both the desktop table
 * (PriceMatrixLanding.tsx) and the mobile card list (PriceCardsMobile.tsx),
 * so category grouping / cheapest-price logic / price formatting stay in
 * sync between breakpoints instead of being copy-pasted twice.
 */

// Unified with the next-intl URL locale codes (frontend/src/i18n.ts) as of
// Phase 4.6 — previously this was a separate 'ru'|'uk'|'en' type that had to
// be bridged back and forth against the URL locale everywhere it crossed a
// component boundary. Now the URL segment IS the Lang value, no bridge.
export type Lang = 'ukr' | 'rus' | 'mne' | 'srb' | 'bos' | 'eng';

export const ALL_LANGS: Lang[] = ['ukr', 'rus', 'mne', 'srb', 'bos', 'eng'];

// Proper BCP-47 tags for the <html lang> attribute — the URL locale codes
// (ukr/rus/mne/srb/bos/eng) are project-internal, not valid BCP-47 on their
// own (e.g. "eng" should render as "en").
export const BCP47_TAG: Record<Lang, string> = {
  ukr: 'uk',
  rus: 'ru',
  mne: 'sr-ME',
  srb: 'sr',
  bos: 'bs',
  eng: 'en',
};

export const LANG_LABEL: Record<Lang, string> = {
  ukr: 'UKR',
  rus: 'РУС',
  mne: 'CG',
  srb: 'SRB',
  bos: 'BiH',
  eng: 'ENG',
};

export interface MatrixProduct {
  id?: string;
  name: string;
  unit: string;
  prices: (number | null)[];
  imageUrl?: string | null;
  category?: string | null;
}

export interface MatrixStore {
  name: string;
  initial: string;
  color: string;
}

// Fallback store list used before the real /matrix-cached fetch resolves,
// and by standalone pages (e.g. the shared shopping-list view) that don't
// have the live `stores` array from the landing page's fetch on hand.
export const DEFAULT_STORES: MatrixStore[] = [
  { name: 'Aroma', initial: 'A', color: '#e11d48' },
  { name: 'Voli', initial: 'V', color: '#2563eb' },
  { name: 'HDL', initial: 'H', color: '#d97706' },
  { name: 'IDEA', initial: 'I', color: '#0891b2' },
];

export const translations: Record<
  Lang,
  {
    product: string;
    cheapest: string;
    updated: string;
    other: string;
    refresh: string;
    refreshing: string;
  }
> = {
  rus: {
    product: 'Товар',
    cheapest: 'Дешевле всего',
    updated: 'Обновлено сегодня',
    other: 'Другое',
    refresh: 'Обновить цены',
    refreshing: 'Обновляем…',
  },
  ukr: {
    product: 'Товар',
    cheapest: 'Найдешевше',
    updated: 'Оновлено сьогодні',
    other: 'Інше',
    refresh: 'Оновити ціни',
    refreshing: 'Оновлюємо…',
  },
  eng: {
    product: 'Product',
    cheapest: 'Cheapest',
    updated: 'Updated today',
    other: 'Other',
    refresh: 'Refresh prices',
    refreshing: 'Refreshing…',
  },
  mne: {
    product: 'Proizvod',
    cheapest: 'Najjeftinije',
    updated: 'Ažurirano danas',
    other: 'Ostalo',
    refresh: 'Osvježi cijene',
    refreshing: 'Osvježavamo…',
  },
  srb: {
    product: 'Proizvod',
    cheapest: 'Najjeftinije',
    updated: 'Ažurirano danas',
    other: 'Ostalo',
    refresh: 'Osveži cene',
    refreshing: 'Osvežavamo…',
  },
  bos: {
    product: 'Proizvod',
    cheapest: 'Najjeftinije',
    updated: 'Ažurirano danas',
    other: 'Ostalo',
    refresh: 'Osvježi cijene',
    refreshing: 'Osvježavamo…',
  },
};

export const formatPrice = (price: number | null, lang: Lang): string => {
  if (price === null) return '—';
  if (lang === 'eng') {
    return `€${price.toFixed(2)}`;
  }
  return `€ ${price.toFixed(2).replace('.', ',')}`;
};

// Matches backend/app/services/category_map.py CATEGORY_ORDER — kept in sync
// manually since the frontend only receives the already-classified label.
export const CATEGORY_ORDER = [
  'Овочі',
  'Фрукти',
  'Фрукти та овочі',
  'Молочка',
  'Бакалія',
  'Дитячі товари',
  "М'ясо і риба",
  'Солодощі та снеки',
  'Напої',
  'Особиста гігієна',
  'Побутова хімія',
  'Акції',
  'Інше',
];

export interface CategoryGroup<T> {
  name: string;
  rows: T[];
}

export function groupByCategory<T extends { category?: string | null }>(
  list: T[],
  otherLabel: string
): CategoryGroup<T>[] {
  const buckets = new Map<string, T[]>();
  for (const row of list) {
    const key = row.category || otherLabel;
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key)!.push(row);
  }
  return Array.from(buckets.entries())
    .map(([name, rows]) => ({ name, rows }))
    .sort((a, b) => {
      const ai = CATEGORY_ORDER.indexOf(a.name);
      const bi = CATEGORY_ORDER.indexOf(b.name);
      return (ai === -1 ? CATEGORY_ORDER.length : ai) - (bi === -1 ? CATEGORY_ORDER.length : bi);
    });
}

export interface WithCheapest {
  minPrice: number | null;
  cheapestIndex: number;
  cheapestStoreName: string;
}

/** Adds min-price / cheapest-store-index to each product. Uses `??` (not
 * `||`) so a cheapest index of 0 (the first store) isn't coerced to -1. */
export function withCheapest<T extends MatrixProduct>(
  products: T[],
  stores: MatrixStore[]
): (T & WithCheapest)[] {
  return products.map((product) => {
    const valid = product.prices
      .map((price, index) => ({ price, index }))
      .filter((p): p is { price: number; index: number } => p.price !== null);

    if (valid.length === 0) {
      return { ...product, minPrice: null, cheapestIndex: -1, cheapestStoreName: '—' };
    }

    const minPrice = Math.min(...valid.map((p) => p.price));
    const cheapestIndex = valid.find((p) => p.price === minPrice)?.index ?? -1;

    return {
      ...product,
      minPrice,
      cheapestIndex,
      cheapestStoreName: stores[cheapestIndex]?.name || '—',
    };
  });
}