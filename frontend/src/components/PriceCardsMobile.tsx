/**
 * PriceCardsMobile — mobile counterpart to PriceMatrixLanding.tsx
 *
 * Recreated from `design_handoff_monte_shop_price_landing/README-mobile.md`
 * (visual reference only, not copied from the .dc.html): the desktop matrix
 * (products=rows, stores=columns) doesn't fit a 390px screen, so each
 * product becomes a stacked card — top row = name/unit + best price/store,
 * bottom row = a compact per-store price strip with the same cheapest-cell
 * highlight logic as the desktop table.
 *
 * Shares category grouping / cheapest-price calc / price formatting with
 * PriceMatrixLanding via lib/productMatrix.ts so both stay in sync.
 *
 * Rendered alongside PriceMatrixLanding (both always mount; Tailwind's
 * `md:hidden` / `hidden md:block` pick one per breakpoint - no JS media
 * query, no hydration mismatch).
 */

'use client';

import { useMemo } from 'react';
import {
  type MatrixProduct as Product,
  type MatrixStore as Store,
  type Lang,
  translations,
  formatPrice,
  groupByCategory,
  withCheapest,
} from '@/lib/productMatrix';

interface PriceCardsMobileProps {
  products: Product[];
  stores: Store[];
  lang: Lang;
  accent?: string;
  onRefreshPrices?: () => void;
  refreshing?: boolean;
}

export function PriceCardsMobile({
  products,
  stores,
  lang = 'ukr',
  accent = '#0b6e4f',
  onRefreshPrices,
  refreshing = false,
}: PriceCardsMobileProps) {
  const t = translations[lang];

  const productsWithCheapest = useMemo(() => withCheapest(products, stores), [products, stores]);

  const hasCategories = productsWithCheapest.some((p) => !!p.category);
  const groups = hasCategories
    ? groupByCategory(productsWithCheapest, t.other)
    : [{ name: '', rows: productsWithCheapest }];

  return (
    <div className="md:hidden w-full">
      {/* Store chip strip — horizontally scrollable */}
      <div className="flex gap-2 overflow-x-auto pb-1 mb-4 -mx-1 px-1" style={{ scrollbarWidth: 'none' }}>
        {stores.map((store) => (
          <div
            key={store.name}
            className="flex items-center gap-1.5 bg-white border rounded-full py-1.5 pl-1.5 pr-3 flex-none"
            style={{ borderColor: '#e3eee8' }}
          >
            <span
              className="flex items-center justify-center w-5 h-5 rounded text-[10px] font-bold text-white"
              style={{ backgroundColor: store.color, fontFamily: 'Space Grotesk, monospace' }}
            >
              {store.initial}
            </span>
            <span className="text-xs font-semibold whitespace-nowrap" style={{ color: '#0f1419' }}>
              {store.name}
            </span>
          </div>
        ))}
      </div>

      {/* Price list header: title + refresh (left), updated (right) */}
      <div className="flex items-center justify-between gap-2 mb-3 px-1">
        <div className="flex items-center gap-2 min-w-0">
          <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: accent }} />
          <span className="font-bold text-base truncate" style={{ color: '#0f3d2e' }}>
            {t.product}
          </span>
          {onRefreshPrices && (
            <button
              onClick={onRefreshPrices}
              disabled={refreshing}
              className="flex items-center gap-1.5 rounded-full flex-shrink-0"
              style={{
                padding: '5px 10px',
                border: `1px solid ${refreshing ? '#d9e7df' : accent}`,
                backgroundColor: refreshing ? '#eafaf1' : 'white',
                color: accent,
                fontSize: '11px',
                fontWeight: 700,
                cursor: refreshing ? 'default' : 'pointer',
              }}
            >
              <span
                className="inline-block"
                style={{ animation: refreshing ? 'monteShopSpin 0.8s linear infinite' : 'none' }}
              >
                ⟳
              </span>
              <span className="whitespace-nowrap">{refreshing ? t.refreshing : t.refresh}</span>
            </button>
          )}
        </div>
        <span
          className="text-[11px] flex-shrink-0"
          style={{ color: '#7d9a8d', fontFamily: 'Space Grotesk, monospace', fontWeight: 500 }}
        >
          {t.updated}
        </span>
      </div>

      {/* Category groups + price cards */}
      {groups.map((group, groupIdx) => (
        <div key={group.name || `group-${groupIdx}`}>
          {group.name && (
            <div
              className="text-xs font-bold uppercase tracking-wide mb-2 mt-3 px-3 py-2 rounded"
              style={{ color: '#33524a', backgroundColor: '#eef4f1', letterSpacing: '0.05em' }}
            >
              {group.name} · {group.rows.length}
            </div>
          )}
          {group.rows.map((product, idx) => (
            <div
              key={idx}
              className="bg-white border rounded mb-2.5 overflow-hidden"
              style={{ borderColor: '#e3eee8' }}
            >
              {/* Name/unit + best price */}
              <div
                className="flex items-center justify-between gap-3 px-3.5 py-3 border-b"
                style={{ borderColor: '#f0f0f0' }}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  {product.imageUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={product.imageUrl}
                      alt=""
                      className="w-7 h-7 rounded object-cover flex-shrink-0"
                      style={{ border: '1px solid #eef4f1' }}
                    />
                  ) : null}
                  <div className="min-w-0">
                    <div className="font-semibold text-sm truncate" style={{ color: '#0f1419' }}>
                      {product.name}
                    </div>
                    <div
                      className="text-[11px] mt-0.5"
                      style={{ color: '#7d9a8d', fontFamily: 'Space Grotesk, monospace' }}
                    >
                      {product.unit}
                    </div>
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <div
                    className="text-base font-bold"
                    style={{ color: accent, fontFamily: 'Space Grotesk, monospace' }}
                  >
                    {formatPrice(product.minPrice, lang)}
                  </div>
                  <div
                    className="text-[10px] uppercase font-medium mt-0.5"
                    style={{ color: '#7d9a8d', letterSpacing: '0.04em' }}
                  >
                    {t.cheapest} · {product.cheapestStoreName}
                  </div>
                </div>
              </div>

              {/* Per-store mini price strip */}
              <div className="flex">
                {stores.map((store, i) => {
                  const price = product.prices[i];
                  const isCheapest = i === product.cheapestIndex && price !== null;
                  return (
                    <div
                      key={store.name}
                      className="flex-1 text-center py-2 px-1.5 border-r last:border-r-0"
                      style={{
                        borderColor: '#f0f0f0',
                        backgroundColor: isCheapest ? '#d8f3e3' : 'transparent',
                        boxShadow: isCheapest ? `inset 0 2px 0 ${accent}` : 'none',
                      }}
                    >
                      <div
                        className="text-[10px] font-semibold mb-0.5"
                        style={{ color: isCheapest ? '#33524a' : '#7d9a8d' }}
                      >
                        {store.initial}
                      </div>
                      <div
                        className="text-xs"
                        style={{
                          fontFamily: 'Space Grotesk, monospace',
                          fontWeight: isCheapest ? 700 : 400,
                          color: price === null ? '#ccc' : isCheapest ? '#05603a' : '#52736a',
                        }}
                      >
                        {price === null ? '—' : formatPrice(price, lang)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}