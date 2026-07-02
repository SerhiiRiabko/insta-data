/**
 * LandingPageDesignBrief — Variant A (Photo-forward)
 *
 * Professional design implementation from design_handoff_monte_shop_price_landing
 *
 * **Variant A — Floating panel over photo**
 * - White header: logo (left), nav (center), language selector (right)
 * - Full-width hero: Kotor Bay photo + green gradient overlay (linear-gradient 180deg)
 * - Centered hero content: kicker → H1 → tagline → search bar
 * - Price matrix "floats" over photo bottom (margin-top: -118px)
 *
 * Colors (per design handoff):
 * - Accent: #0b6e4f (brand green)
 * - Deep: #0f3d2e (headings)
 * - Cheapest bg: #d8f3e3
 * - Typography: Plus Jakarta Sans (UI) + Space Grotesk (prices)
 *
 * Updated: 2026-06-30 — ✅ Variant A implemented
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { PriceMatrixLanding } from './PriceMatrixLanding';
import { ProductsModal } from './ProductsModal';
import { StoresModal } from './StoresModal';
import { AboutModal } from './AboutModal';
import { productsAPI } from '@/lib/api';

type Lang = 'ru' | 'uk' | 'en';

// Mock product data — fallback when backend unavailable
const MOCK_PRODUCTS = [
  { name: 'Молоко / Молоко / Milk', unit: '1 л', prices: [1.49, 1.45, 1.52, 1.39] },
  { name: 'Хлеб / Хліб / Bread', unit: '500 г', prices: [0.89, 0.95, 0.85, 0.92] },
  { name: 'Яйца / Яйця / Eggs', unit: '10 шт', prices: [2.49, 2.39, 2.55, 2.45] },
  { name: 'Сыр Гауда / Сир Гауда / Gouda cheese', unit: '1 кг', prices: [8.90, 9.20, 8.45, 8.99] },
  { name: 'Бананы / Банани / Bananas', unit: '1 кг', prices: [1.29, 1.19, 1.35, 1.25] },
  { name: 'Кофе молотый / Кава мелена / Ground coffee', unit: '250 г', prices: [4.49, 4.29, 4.59, 4.19] },
  { name: 'Оливковое масло / Оливкова олія / Olive oil', unit: '1 л', prices: [6.99, 7.49, 6.79, 7.10] },
  { name: 'Вода / Вода / Water', unit: '1,5 л', prices: [0.55, 0.59, 0.49, 0.52] },
];

const MOCK_STORES = [
  { name: 'Aroma', initial: 'A', color: '#e11d48' },
  { name: 'Voli', initial: 'V', color: '#2563eb' },
  { name: 'HDL', initial: 'H', color: '#d97706' },
  { name: 'IDEA', initial: 'I', color: '#0891b2' },
  { name: 'Instagram', initial: 'IG', color: '#e1306c' }, // Phase 3: 5th source
];

const TRANSLATIONS = {
  ru: {
    kicker: 'Цены в реальном времени',
    tagline: 'Сравнение цен на продукты в супермаркетах Черногории',
    heroLine: 'Monte-Shop-Price',
    searchPlaceholder: 'Поиск товара…',
    searchBtn: 'Найти',
    nav: ['Товары', 'Магазины', 'О проекте'],
    tableTitle: 'Сравнение цен',
    tableSub: 'по 5 источникам (4 магазина + Instagram)',
    product: 'Товар',
    cheapest: 'Дешевле всего',
    updated: 'Обновлено сегодня',
  },
  uk: {
    kicker: 'Ціни в реальному часі',
    tagline: 'Порівняння цін на продукти в супермаркетах Чорногорії',
    heroLine: 'Monte-Shop-Price',
    searchPlaceholder: 'Пошук товару…',
    searchBtn: 'Знайти',
    nav: ['Товари', 'Магазини', 'Про проєкт'],
    tableTitle: 'Порівняння цін',
    tableSub: 'по 5 джерелам (4 магазини + Instagram)',
    product: 'Товар',
    cheapest: 'Найдешевше',
    updated: 'Оновлено сьогодні',
  },
  en: {
    kicker: 'Real-time prices',
    tagline: 'Real-time grocery price comparison across Montenegro',
    heroLine: 'Monte-Shop-Price',
    searchPlaceholder: 'Search a product…',
    searchBtn: 'Search',
    nav: ['Products', 'Stores', 'About'],
    tableTitle: 'Price comparison',
    tableSub: 'across 5 sources (4 stores + Instagram)',
    product: 'Product',
    cheapest: 'Cheapest',
    updated: 'Updated today',
  },
};

const KOTOR_URL =
  'https://commons.wikimedia.org/wiki/Special:FilePath/Vista_de_Kotor,_Bah%C3%ADa_de_Kotor,_Montenegro,_2014-04-19,_DD_25.JPG?width=2000';

function VariationA({
  lang,
  setLang,
  t,
  onProductsClick,
  onStoresClick,
  onAboutClick,
  products,
  stores,
  loading,
}: {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: any;
  onProductsClick: () => void;
  onStoresClick: () => void;
  onAboutClick: () => void;
  products: any[];
  stores: any[];
  loading: boolean;
}) {
  return (
    <div style={{ backgroundColor: '#f5f3f0', minHeight: '100vh' }}>
      {/* WHITE HEADER — logo (left) | nav (center) | language (right) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '24px 44px',
          backgroundColor: 'white',
          borderBottom: '1px solid #eef4f1',
        }}
      >
        {/* Left: Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '4px',
              backgroundColor: '#0b6e4f',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 'bold',
              fontSize: '18px',
            }}
          >
            M
          </div>
          <span style={{ fontWeight: '600', fontSize: '16px', color: '#0f3d2e' }}>
            Monte-Shop-Price
          </span>
        </div>

        {/* Center: Nav Links */}
        <div style={{ display: 'flex', gap: '32px' }}>
          {t.nav.map((label: string, idx: number) => (
            <button
              key={idx}
              onClick={[onProductsClick, onStoresClick, onAboutClick][idx]}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '14px',
                fontWeight: '500',
                color: '#52736a',
                cursor: 'pointer',
                transition: 'color 120ms',
              }}
              onMouseEnter={(e) => {
                (e.target as HTMLButtonElement).style.color = '#0b6e4f';
              }}
              onMouseLeave={(e) => {
                (e.target as HTMLButtonElement).style.color = '#52736a';
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Right: Language Selector */}
        <div style={{ display: 'flex', gap: '2px' }}>
          {(['ru', 'uk', 'en'] as Lang[]).map((l) => (
            <button
              key={l}
              onClick={() => setLang(l)}
              style={{
                padding: '6px 12px',
                border: lang === l ? 'none' : '1px solid #d0d9d5',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: '700',
                backgroundColor: lang === l ? '#0b6e4f' : 'white',
                color: lang === l ? 'white' : '#0f3d2e',
                cursor: 'pointer',
                transition: 'all 120ms cubic-bezier(0.2,0,0,1)',
              }}
            >
              {l.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* FULL-WIDTH HERO — Photo + Gradient Overlay */}
      <div
        style={{
          backgroundImage: `linear-gradient(180deg, rgba(6,78,59,0.5) 0%, rgba(6,78,59,0.22) 38%, rgba(6,78,59,0.82) 100%), url('${KOTOR_URL}')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center 38%',
          paddingBottom: '150px',
          paddingTop: '72px',
          textAlign: 'center',
          minHeight: '500px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Kicker */}
        <div
          style={{
            display: 'inline-block',
            padding: '8px 16px',
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '999px',
            fontSize: '12px',
            fontWeight: '600',
            color: 'white',
            marginBottom: '32px',
            backdropFilter: 'blur(8px)',
          }}
        >
          {t.kicker}
        </div>

        {/* H1 */}
        <h1
          style={{
            fontSize: '58px',
            fontWeight: '800',
            color: 'white',
            margin: '0 0 16px 0',
            letterSpacing: '-0.025em',
            textShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
            maxWidth: '800px',
          }}
        >
          {t.heroLine}
        </h1>

        {/* Tagline */}
        <p
          style={{
            fontSize: '19px',
            fontWeight: '500',
            color: 'rgba(255, 255, 255, 0.95)',
            margin: '0 0 40px 0',
            maxWidth: '640px',
            lineHeight: '1.6',
            textShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
          }}
        >
          {t.tagline}
        </p>

        {/* Search Bar */}
        <form
          onSubmit={(e) => e.preventDefault()}
          style={{
            display: 'flex',
            gap: '0',
            maxWidth: '640px',
            width: '100%',
            boxShadow: '0 24px 50px -22px rgba(6,40,28,0.55)',
          }}
        >
          <input
            type="text"
            placeholder={t.searchPlaceholder}
            style={{
              flex: 1,
              padding: '14px 20px',
              border: 'none',
              borderRadius: '10px 0 0 10px',
              fontSize: '14px',
              fontFamily: 'inherit',
            }}
          />
          <button
            style={{
              padding: '14px 24px',
              backgroundColor: '#0b6e4f',
              color: 'white',
              border: 'none',
              borderRadius: '0 10px 10px 0',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'background-color 120ms',
            }}
            onMouseEnter={(e) => {
              (e.target as HTMLButtonElement).style.backgroundColor = '#084d35';
            }}
            onMouseLeave={(e) => {
              (e.target as HTMLButtonElement).style.backgroundColor = '#0b6e4f';
            }}
          >
            {t.searchBtn}
          </button>
        </form>
      </div>

      {/* FLOATING MATRIX — Centered */}
      <div
        style={{
          position: 'relative',
          marginTop: '40px',
          paddingLeft: '44px',
          paddingRight: '44px',
          paddingBottom: '52px',
          zIndex: 10,
          boxSizing: 'border-box',
          width: '100%',
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <div style={{ width: '100%', maxWidth: '1400px' }}>
          {loading ? (
            <div
              style={{
                background: 'white',
                borderRadius: '18px',
                padding: '24px',
                textAlign: 'center',
                color: '#999',
              }}
            >
              Завантажуємо ціни...
            </div>
          ) : (
            <PriceMatrixLanding products={products} stores={stores} lang={lang} accent="#0b6e4f" />
          )}
        </div>
      </div>
    </div>
  );
}

export function LandingPageDesignBrief() {
  const [lang, setLang] = useState<Lang>('ru');
  const [isProductsOpen, setIsProductsOpen] = useState(false);
  const [isStoresOpen, setIsStoresOpen] = useState(false);
  const [isAboutOpen, setIsAboutOpen] = useState(false);

  // Backend Integration (Phase 1)
  const [products, setProducts] = useState(MOCK_PRODUCTS);
  const [stores, setStores] = useState(MOCK_STORES);
  const [loading, setLoading] = useState(true);

  const t = TRANSLATIONS[lang];

  // Fetch price matrix from backend (Phase 3: Live scraper data)
  useEffect(() => {
    const fetchMatrix = async () => {
      try {
        setLoading(true);

        // Try live endpoint first (67 products from 5 sources)
        try {
          const response = await productsAPI.priceMatrixLive();
          const data = response.data;

          if (data && data.stores && data.products) {
            setStores(data.stores);
            setProducts(
              data.products.map((p: any) => ({
                id: p.id,
                name: p.name,
                unit: p.unit,
                prices: p.prices,
              }))
            );
            console.log(`Loaded ${data.products.length} products from live endpoint`);
            return;
          }
        } catch (liveErr) {
          console.warn('Live endpoint failed, falling back to mock:', liveErr);
        }

        // Fallback to old endpoint if live fails
        const response = await productsAPI.priceMatrix(lang);
        const data = response.data;

        if (data && data.stores && data.products) {
          setStores(data.stores);
          setProducts(
            data.products.map((p: any) => ({
              id: p.id,
              name: p.name,
              unit: p.unit,
              prices: p.prices,
            }))
          );
        }
      } catch (err) {
        console.error('Failed to fetch price matrix:', err);
        // Keep mock data as fallback
      } finally {
        setLoading(false);
      }
    };

    fetchMatrix();
  }, []);

  const onProductsClick = useCallback(() => setIsProductsOpen(true), []);
  const onStoresClick = useCallback(() => setIsStoresOpen(true), []);
  const onAboutClick = useCallback(() => setIsAboutOpen(true), []);

  return (
    <>
      <VariationA
        lang={lang}
        setLang={setLang}
        t={t}
        onProductsClick={onProductsClick}
        onStoresClick={onStoresClick}
        onAboutClick={onAboutClick}
        products={products}
        stores={stores}
        loading={loading}
      />

      {/* Modals */}
      <ProductsModal
        isOpen={isProductsOpen}
        onClose={() => setIsProductsOpen(false)}
        products={products}
        lang={lang}
      />
      <StoresModal isOpen={isStoresOpen} onClose={() => setIsStoresOpen(false)} lang={lang} />
      <AboutModal isOpen={isAboutOpen} onClose={() => setIsAboutOpen(false)} lang={lang} />
    </>
  );
}