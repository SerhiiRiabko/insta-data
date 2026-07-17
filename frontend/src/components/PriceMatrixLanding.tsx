/**
 * PriceMatrixLanding — Price Comparison Table Component
 *
 * Розташування: Monte-Shop-Price Variant C (Immersive landing)
 *
 * Функціональність:
 * - HTML <table> для порівняння цін по 4 магазинам
 * - Товари як рядки, магазини (Aroma, Voli, HDL, IDEA) як стовпці
 * - Виділення найдешевшої ціни в кожному рядку (зелене + accent border)
 * - Обробка null prices (товари не доступні в деяких магазинах)
 * - Локалізація цін (EUR з комою для RU/UK, крапка для EN)
 * - Вертикальні + горизонтальні лінії розділення для читаємості
 *
 * Дизайн:
 * - Inline CSS styles (гарантує рендеринг, обходить Tailwind CSS limitation)
 * - Білий контейнер (bg-white/99) з backdrop-blur
 * - Сірий фон 30% opacity навколо таблиці (родител контейнер)
 * - Font sizes: 20px headers, 32px prices, 24px product names
 * - Color scheme: #0f3d2e (deep green), #0b6e4f (accent), #d8f3e3 (cheapest bg)
 *
 * Updated: 2026-06-23 — Переписано на inline CSS for proper rendering
 */

'use client';

import { Fragment, useMemo } from 'react';
import {
  type MatrixProduct as Product,
  type MatrixStore as Store,
  type Lang,
  translations,
  formatPrice,
  groupByCategory,
  withCheapest,
} from '@/lib/productMatrix';

interface PriceMatrixProps {
  products: Product[];
  stores: Store[];
  lang: Lang;
  accent?: string;
  onRefreshPrices?: () => void;
  refreshing?: boolean;
}

export function PriceMatrixLanding({
  products,
  stores,
  lang = 'ukr',
  accent = '#0b6e4f',
  onRefreshPrices,
  refreshing = false,
}: PriceMatrixProps) {
  const t = translations[lang];

  const productsWithCheapest = useMemo(() => withCheapest(products, stores), [products, stores]);

  const hasCategories = productsWithCheapest.some((p) => !!p.category);

  const groups = hasCategories
    ? groupByCategory(productsWithCheapest, t.other)
    : [{ name: '', rows: productsWithCheapest }];

  const colSpan = stores.length + 2; // product column + cheapest column

  return (
    <div className="hidden md:block w-full bg-white backdrop-blur-md rounded-3xl border border-gray-300 shadow-2xl overflow-hidden" style={{ boxShadow: '0 28px 64px -30px rgba(6,78,59,0.4)' }}>
      {/* Header Bar — per design handoff */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '20px 24px',
          borderBottom: '1px solid #eef4f1',
          backgroundColor: '#ffffff',
          width: '100%',
          boxSizing: 'border-box',
        }}
      >
        {/* Left: accent dot + title + refresh button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span
            style={{
              width: '9px',
              height: '9px',
              borderRadius: '50%',
              backgroundColor: accent,
            }}
          ></span>
          <span style={{ fontSize: '17px', fontWeight: '700', color: '#0f3d2e' }}>
            {t.product}
          </span>
          {onRefreshPrices && (
            <button
              onClick={onRefreshPrices}
              disabled={refreshing}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '999px',
                border: `1px solid ${refreshing ? '#d9e7df' : accent}`,
                backgroundColor: refreshing ? '#eafaf1' : 'white',
                color: accent,
                fontSize: '12px',
                fontWeight: '700',
                cursor: refreshing ? 'default' : 'pointer',
                transition: 'background-color 120ms',
              }}
            >
              <span
                style={{
                  display: 'inline-block',
                  animation: refreshing ? 'monteShopSpin 0.8s linear infinite' : 'none',
                }}
              >
                ⟳
              </span>
              {refreshing ? t.refreshing : t.refresh}
            </button>
          )}
        </div>
        {/* Right: updated text */}
        <span
          style={{
            fontSize: '13px',
            fontWeight: '500',
            color: '#7d9a8d',
            fontFamily: 'monospace',
          }}
        >
          {t.updated}
        </span>
      </div>

      {/* Table — scrolls internally, store-header row stays pinned via sticky thead */}
      <div style={{ overflowY: 'auto', overflowX: 'hidden', width: '100%', maxHeight: '70vh' }}>
        <table className="w-full" style={{ borderCollapse: 'collapse', tableLayout: 'fixed' }}>
          <thead style={{ position: 'sticky', top: 0, zIndex: 2 }}>
            <tr style={{ backgroundColor: '#f6faf8', borderBottom: '2px solid #d9e7df' }}>
              {/* Product Column */}
              <th
                style={{
                  textAlign: 'left',
                  paddingLeft: '16px',
                  paddingRight: '16px',
                  paddingTop: '16px',
                  paddingBottom: '16px',
                  fontSize: '12px',
                  fontWeight: '600',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: '#6b8a7d',
                  borderRight: '1px solid #d9e7df',
                  width: '24%',
                }}
              >
                {t.product}
              </th>

              {/* Store Headers */}
              {stores.map((store) => (
                <th
                  key={store.name}
                  style={{
                    textAlign: 'right',
                    paddingLeft: '10px',
                    paddingRight: '10px',
                    paddingTop: '16px',
                    paddingBottom: '16px',
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#33524a',
                    borderRight: '1px solid #d9e7df',
                    whiteSpace: 'nowrap',
                    width: '16%',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px' }}>
                    <span
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '24px',
                        height: '24px',
                        borderRadius: '7px',
                        backgroundColor: store.color,
                        color: 'white',
                        fontWeight: '700',
                        fontSize: '12px',
                      }}
                    >
                      {store.initial}
                    </span>
                    <span>{store.name}</span>
                  </div>
                </th>
              ))}

              {/* Cheapest Column */}
              <th
                style={{
                  textAlign: 'right',
                  paddingLeft: '10px',
                  paddingRight: '10px',
                  paddingTop: '16px',
                  paddingBottom: '16px',
                  fontSize: '11px',
                  fontWeight: '700',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: '#0b6e4f',
                  backgroundColor: '#eafaf1',
                  borderLeft: '1px solid #e3eee8',
                  width: '12%',
                }}
              >
                {t.cheapest}
              </th>
            </tr>
          </thead>

          <tbody>
            {groups.map((group, groupIdx) => (
              <Fragment key={group.name || `group-${groupIdx}`}>
                {group.name && (
                  <tr>
                    <td
                      colSpan={colSpan}
                      style={{
                        textAlign: 'left',
                        padding: '10px 16px',
                        fontSize: '12px',
                        fontWeight: '700',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                        color: '#33524a',
                        backgroundColor: '#eef4f1',
                        borderTop: '1px solid #d9e7df',
                        borderBottom: '1px solid #d9e7df',
                      }}
                    >
                      {group.name} · {group.rows.length}
                    </td>
                  </tr>
                )}
                {group.rows.map((product, rowIdx) => (
              <tr key={rowIdx} style={{ borderBottom: '1px solid #eef4f1' }}>
                {/* Product Name Cell */}
                <td
                  style={{
                    textAlign: 'left',
                    paddingLeft: '16px',
                    paddingRight: '16px',
                    paddingTop: '15px',
                    paddingBottom: '15px',
                    borderRight: '1px solid #eef4f1',
                    width: '24%',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {product.imageUrl ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={product.imageUrl}
                        alt=""
                        width={28}
                        height={28}
                        style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: '6px',
                          objectFit: 'cover',
                          border: '1px solid #eef4f1',
                          flexShrink: 0,
                        }}
                      />
                    ) : null}
                    <div>
                      <div style={{ fontSize: '15px', fontWeight: '600', color: '#0f3d2e' }}>
                        {product.name}
                      </div>
                      <div style={{ fontSize: '12px', color: '#94aea3', marginTop: '4px', fontFamily: 'monospace' }}>
                        {product.unit}
                      </div>
                    </div>
                  </div>
                </td>

                {/* Price Cells */}
                {product.prices.map((price, colIdx) => {
                  const isCheapest = colIdx === product.cheapestIndex && price !== null;
                  const isUnavailable = price === null;

                  return (
                    <td
                      key={colIdx}
                      style={{
                        textAlign: 'right',
                        paddingLeft: '10px',
                        paddingRight: '10px',
                        paddingTop: '15px',
                        paddingBottom: '15px',
                        fontSize: '13px',
                        fontWeight: isCheapest ? '700' : '600',
                        fontFamily: 'Space Grotesk, monospace',
                        fontVariantNumeric: 'tabular-nums',
                        color: isUnavailable ? '#ccc' : isCheapest ? '#05603a' : '#52736a',
                        backgroundColor: isCheapest ? '#d8f3e3' : 'white',
                        borderRight: '1px solid #eef4f1',
                        borderLeft: isCheapest ? `3px solid ${accent}` : 'none',
                        width: '16%',
                      }}
                    >
                      {isUnavailable ? '—' : formatPrice(price, lang)}
                    </td>
                  );
                })}

                {/* Cheapest Summary Cell */}
                <td
                  style={{
                    textAlign: 'right',
                    paddingLeft: '10px',
                    paddingRight: '10px',
                    paddingTop: '13px',
                    paddingBottom: '13px',
                    backgroundColor: '#fafdfb',
                    borderLeft: '1px solid #f0f5f2',
                    width: '12%',
                  }}
                >
                  {product.minPrice !== null ? (
                    <div>
                      <div style={{ fontSize: '20px', fontWeight: 'bold', color: accent, fontFamily: 'Space Grotesk, monospace' }}>
                        {formatPrice(product.minPrice, lang)}
                      </div>
                      <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#7a8e8a', fontWeight: 'bold', marginTop: '4px' }}>
                        {product.cheapestStoreName}
                      </div>
                    </div>
                  ) : (
                    <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#bbb' }}>—</div>
                  )}
                </td>
              </tr>
                ))}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}