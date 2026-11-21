'use client';

import { useEffect, useState } from 'react';
import { productsAPI, type Country, type ProductSearchResult } from './api';
import type { Lang } from './productMatrix';

/**
 * Server-side, cross-language product search (debounced): someone browsing
 * Montenegrin stores in Ukrainian types "молоко" and gets "Mlijeko …".
 * Returns null while there's no query or the request is in flight / failed,
 * so callers keep their instant local name filter meanwhile.
 */
export function useProductSearch(query: string, country: Country, lang: Lang, delayMs = 350) {
  const [results, setResults] = useState<ProductSearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setResults(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    const timer = setTimeout(() => {
      productsAPI
        .search(q, country, lang)
        .then((res) => !cancelled && setResults(res.data.results))
        .catch(() => !cancelled && setResults(null))
        .finally(() => !cancelled && setLoading(false));
    }, delayMs);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query, country, lang, delayMs]);

  return { results, loading };
}

/**
 * Filters already-loaded products by a query: the server's ranked matches
 * first (they cover every language), then any local name match the server
 * didn't return.
 */
export function filterBySearch<T extends { id?: string; name: string }>(
  items: T[],
  query: string,
  serverResults: ProductSearchResult[] | null
): T[] {
  const q = query.trim().toLowerCase();
  if (!q) return items;
  const local = items.filter((p) => (p.name ?? '').toLowerCase().includes(q));
  if (!serverResults) return local;
  const byId = new Map(items.filter((p) => p.id).map((p) => [p.id as string, p]));
  const ranked = serverResults.map((r) => byId.get(r.id)).filter((p): p is T => !!p);
  const seen = new Set(ranked);
  return [...ranked, ...local.filter((p) => !seen.has(p))];
}
