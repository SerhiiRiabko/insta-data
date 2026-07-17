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
import { useParams, usePathname, useRouter } from 'next/navigation';
import { PriceMatrixLanding } from './PriceMatrixLanding';
import { PriceCardsMobile } from './PriceCardsMobile';
import { ShoppingListModal } from './ShoppingListModal';
import { StoresModal } from './StoresModal';
import { AboutModal } from './AboutModal';
import { AuthModal } from './AuthModal';
import { productsAPI, authAPI } from '@/lib/api';
import { DEFAULT_STORES, ALL_LANGS, LANG_LABEL, type Lang } from '@/lib/productMatrix';

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

const MOCK_STORES = DEFAULT_STORES;

const TRANSLATIONS: Record<Lang, {
  kicker: string; tagline: string; heroLine: string; searchPlaceholder: string;
  searchBtn: string; nav: string[]; tableTitle: string; tableSub: string;
  product: string; cheapest: string; updated: string; refresh: string; refreshing: string;
  noResults: string;
}> = {
  rus: {
    kicker: 'Цены в реальном времени',
    tagline: 'Сравнение цен на продукты в супермаркетах Черногории',
    heroLine: 'Monte-Shop-Price',
    searchPlaceholder: 'Поиск товара…',
    searchBtn: 'Найти',
    nav: ['Список покупок', 'Магазины', 'О проекте'],
    tableTitle: 'Сравнение цен',
    tableSub: 'по 4 магазинам Черногории',
    product: 'Товар',
    cheapest: 'Дешевле всего',
    updated: 'Обновлено сегодня',
    refresh: 'Обновить цены',
    refreshing: 'Обновляем…',
    noResults: 'Ничего не найдено по запросу',
  },
  ukr: {
    kicker: 'Ціни в реальному часі',
    tagline: 'Порівняння цін на продукти в супермаркетах Чорногорії',
    heroLine: 'Monte-Shop-Price',
    searchPlaceholder: 'Пошук товару…',
    searchBtn: 'Знайти',
    nav: ['Список покупок', 'Магазини', 'Про проєкт'],
    tableTitle: 'Порівняння цін',
    tableSub: 'по 4 магазинах Чорногорії',
    product: 'Товар',
    cheapest: 'Найдешевше',
    updated: 'Оновлено сьогодні',
    refresh: 'Оновити ціни',
    refreshing: 'Оновлюємо…',
    noResults: 'Нічого не знайдено за запитом',
  },
  eng: {
    kicker: 'Real-time prices',
    tagline: 'Real-time grocery price comparison across Montenegro',
    heroLine: 'Monte-Shop-Price',
    searchPlaceholder: 'Search a product…',
    searchBtn: 'Search',
    nav: ['Shopping List', 'Stores', 'About'],
    tableTitle: 'Price comparison',
    tableSub: 'across 4 stores in Montenegro',
    product: 'Product',
    cheapest: 'Cheapest',
    updated: 'Updated today',
    refresh: 'Refresh prices',
    refreshing: 'Refreshing…',
    noResults: 'No products found for',
  },
  mne: {
    kicker: 'Cijene u realnom vremenu',
    tagline: 'Poređenje cijena prehrambenih proizvoda u supermarketima Crne Gore',
    heroLine: 'Monte-Shop-Price',
    searchPlaceholder: 'Pretraga proizvoda…',
    searchBtn: 'Pretraga',
    nav: ['Lista za kupovinu', 'Prodavnice', 'O projektu'],
    tableTitle: 'Poređenje cijena',
    tableSub: 'u 4 prodavnice u Crnoj Gori',
    product: 'Proizvod',
    cheapest: 'Najjeftinije',
    updated: 'Ažurirano danas',
    refresh: 'Osvježi cijene',
    refreshing: 'Osvježavamo…',
    noResults: 'Nema rezultata za',
  },
  srb: {
    kicker: 'Cene u realnom vremenu',
    tagline: 'Poređenje cena prehrambenih proizvoda u supermarketima Crne Gore',
    heroLine: 'Monte-Shop-Price',
    searchPlaceholder: 'Pretraga proizvoda…',
    searchBtn: 'Pretraga',
    nav: ['Lista za kupovinu', 'Prodavnice', 'O projektu'],
    tableTitle: 'Poređenje cena',
    tableSub: 'u 4 prodavnice u Crnoj Gori',
    product: 'Proizvod',
    cheapest: 'Najjeftinije',
    updated: 'Ažurirano danas',
    refresh: 'Osveži cene',
    refreshing: 'Osvežavamo…',
    noResults: 'Nema rezultata za',
  },
  bos: {
    kicker: 'Cijene u realnom vremenu',
    tagline: 'Poređenje cijena prehrambenih proizvoda u supermarketima Crne Gore',
    heroLine: 'Monte-Shop-Price',
    searchPlaceholder: 'Pretraga proizvoda…',
    searchBtn: 'Pretraga',
    nav: ['Lista za kupovinu', 'Prodavnice', 'O projektu'],
    tableTitle: 'Poređenje cijena',
    tableSub: 'u 4 prodavnice u Crnoj Gori',
    product: 'Proizvod',
    cheapest: 'Najjeftinije',
    updated: 'Ažurirano danas',
    refresh: 'Osvježi cijene',
    refreshing: 'Osvježavamo…',
    noResults: 'Nema rezultata za',
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
  onHomeClick,
  onRefreshPrices,
  refreshing,
  products,
  stores,
  loading,
  currentUser,
  onAuthClick,
  onLogoutClick,
  searchQuery,
  onSearchQueryChange,
}: {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: any;
  onProductsClick: () => void;
  onStoresClick: () => void;
  onAboutClick: () => void;
  onHomeClick: () => void;
  onRefreshPrices: () => void;
  refreshing: boolean;
  products: any[];
  stores: any[];
  loading: boolean;
  currentUser: { id: string; email: string; tier: string } | null;
  onAuthClick: () => void;
  onLogoutClick: () => void;
  searchQuery: string;
  onSearchQueryChange: (value: string) => void;
}) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div style={{ backgroundColor: '#f5f3f0', minHeight: '100vh' }}>
      {/* WHITE HEADER — logo (left) | nav (center, desktop only) | language + mobile menu (right). Sticky on mobile per README-mobile.md. */}
      <div
        className="sticky md:static top-0 z-20 flex items-center justify-between gap-2 px-2.5 py-4 min-[400px]:px-4 md:px-11 md:py-6"
        style={{
          backgroundColor: 'white',
          borderBottom: '1px solid #eef4f1',
        }}
      >
        {/* Left: Logo — click to go home (scrolls to top, closes any open modal) */}
        <button
          onClick={onHomeClick}
          aria-label="Monte-Shop-Price — home"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            background: 'none',
            border: 'none',
            padding: 0,
            cursor: 'pointer',
          }}
        >
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
          <span className="hidden min-[360px]:inline" style={{ fontWeight: '600', fontSize: '16px', color: '#0f3d2e' }}>
            Monte-Shop-Price
          </span>
        </button>

        {/* Center: Nav Links (desktop only — mobile uses the ☰ menu below) */}
        <div className="hidden md:flex items-center gap-8">
          {t.nav.map((label: string, idx: number) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
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
              {idx === 0 && (
                <button
                  onClick={onRefreshPrices}
                  disabled={refreshing}
                  title={refreshing ? t.refreshing : t.refresh}
                  aria-label={refreshing ? t.refreshing : t.refresh}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '26px',
                    height: '26px',
                    borderRadius: '50%',
                    border: '1px solid #d9e7df',
                    backgroundColor: refreshing ? '#eafaf1' : 'white',
                    color: '#0b6e4f',
                    cursor: refreshing ? 'default' : 'pointer',
                    fontSize: '13px',
                    lineHeight: 1,
                    padding: 0,
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
                </button>
              )}
            </div>
          ))}
        </div>
        <style>{`
          @keyframes monteShopSpin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}</style>

        {/* Right: Auth + Language Selector + mobile menu toggle */}
        <div className="gap-1.5 min-[400px]:gap-2" style={{ display: 'flex', alignItems: 'center' }}>
          <button
            onClick={currentUser ? onLogoutClick : onAuthClick}
            title={currentUser ? currentUser.email : undefined}
            aria-label={currentUser ? 'Log out' : 'Log in'}
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              border: currentUser ? 'none' : '1px solid #d0d9d5',
              backgroundColor: currentUser ? '#0b6e4f' : 'white',
              color: currentUser ? 'white' : '#0f3d2e',
              fontSize: currentUser ? '13px' : '15px',
              fontWeight: 700,
              cursor: 'pointer',
              flexShrink: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {currentUser ? currentUser.email[0].toUpperCase() : '👤'}
          </button>
          <select
            value={lang}
            onChange={(e) => setLang(e.target.value as Lang)}
            aria-label="Language"
            className="px-2 py-1.5 min-[400px]:px-3"
            style={{
              border: '1px solid #d0d9d5',
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: '700',
              backgroundColor: 'white',
              color: '#0f3d2e',
              cursor: 'pointer',
            }}
          >
            {ALL_LANGS.map((l) => (
              <option key={l} value={l}>
                {LANG_LABEL[l]}
              </option>
            ))}
          </select>
          <button
            className="flex md:hidden"
            onClick={() => setIsMobileMenuOpen((v) => !v)}
            aria-label="Menu"
            aria-expanded={isMobileMenuOpen}
            style={{
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              border: '1px solid #d0d9d5',
              backgroundColor: 'white',
              color: '#0f3d2e',
              fontSize: '15px',
              cursor: 'pointer',
            }}
          >
            {isMobileMenuOpen ? '✕' : '☰'}
          </button>
        </div>
      </div>

      {/* Mobile dropdown — Товари/Магазини/Про проєкт (desktop nav lives in the header above) */}
      {isMobileMenuOpen && (
        <div
          className="md:hidden flex flex-col"
          style={{ backgroundColor: 'white', borderBottom: '1px solid #eef4f1', padding: '4px 16px 12px' }}
        >
          {t.nav.map((label: string, idx: number) => (
            <button
              key={idx}
              onClick={() => {
                [onProductsClick, onStoresClick, onAboutClick][idx]();
                setIsMobileMenuOpen(false);
              }}
              style={{
                background: 'none',
                border: 'none',
                borderTop: idx > 0 ? '1px solid #f0f5f2' : 'none',
                textAlign: 'left',
                fontSize: '14px',
                fontWeight: 500,
                color: '#33524a',
                padding: '12px 4px',
                cursor: 'pointer',
                width: '100%',
              }}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {/* FULL-WIDTH HERO — Photo + Gradient Overlay. Sizing/spacing scale down on mobile per README-mobile.md. */}
      <div
        className="px-5 pt-10 pb-14 md:px-0 md:pt-[72px] md:pb-[150px] min-h-0 md:min-h-[500px]"
        style={{
          backgroundImage: `linear-gradient(180deg, rgba(6,78,59,0.5) 0%, rgba(6,78,59,0.22) 38%, rgba(6,78,59,0.82) 100%), url('${KOTOR_URL}')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center 38%',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Kicker */}
        <div
          className="mb-4 md:mb-8"
          style={{
            display: 'inline-block',
            padding: '8px 16px',
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '999px',
            fontSize: '12px',
            fontWeight: '600',
            color: 'white',
            backdropFilter: 'blur(8px)',
          }}
        >
          {t.kicker}
        </div>

        {/* H1 */}
        <h1
          className="text-[32px] md:text-[58px] mb-3 md:mb-4"
          style={{
            fontWeight: '800',
            color: 'white',
            margin: '0',
            letterSpacing: '-0.025em',
            textShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
            maxWidth: '800px',
          }}
        >
          {t.heroLine}
        </h1>

        {/* Tagline */}
        <p
          className="text-[15px] md:text-[19px] mb-6 md:mb-10"
          style={{
            fontWeight: '500',
            color: 'rgba(255, 255, 255, 0.95)',
            margin: '0',
            maxWidth: '640px',
            lineHeight: '1.6',
            textShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
          }}
        >
          {t.tagline}
        </p>

        {/* Search Bar — stacked card on mobile, joined pill row on desktop */}
        <form
          onSubmit={(e) => e.preventDefault()}
          className="flex flex-col gap-2 bg-white p-2 rounded-md shadow-[0_20px_40px_-16px_rgba(15,20,25,0.2)] md:flex-row md:gap-0 md:bg-transparent md:p-0 md:rounded-none md:shadow-[0_24px_50px_-22px_rgba(6,40,28,0.55)]"
          style={{ maxWidth: '640px', width: '100%' }}
        >
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            placeholder={t.searchPlaceholder}
            aria-label={t.searchPlaceholder}
            className="flex-1 w-full rounded md:rounded-l-[10px] md:rounded-r-none text-base md:text-sm"
            style={{
              padding: '14px 20px',
              border: '1px solid rgba(15, 20, 25, 0.25)',
              outline: 'none',
              fontFamily: 'inherit',
              backgroundColor: 'rgba(120, 130, 128, 0.3)',
              color: '#0f1419',
            }}
          />
          <button
            className="w-full md:w-auto rounded md:rounded-r-[10px] md:rounded-l-none text-sm"
            style={{
              padding: '14px 24px',
              backgroundColor: '#0b6e4f',
              color: 'white',
              border: 'none',
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

      {/* FLOATING MATRIX — Centered (desktop table + mobile card list, CSS-toggled) */}
      <div
        className="px-4 md:px-11 pb-10 md:pb-[52px] mt-6 md:mt-10"
        style={{
          position: 'relative',
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
          ) : searchQuery.trim() && products.length === 0 ? (
            <div
              style={{
                background: 'white',
                borderRadius: '18px',
                padding: '24px',
                textAlign: 'center',
                color: '#999',
              }}
            >
              {t.noResults} &laquo;{searchQuery.trim()}&raquo;
            </div>
          ) : (
            <>
              <PriceMatrixLanding
                products={products}
                stores={stores}
                lang={lang}
                accent="#0b6e4f"
                onRefreshPrices={onRefreshPrices}
                refreshing={refreshing}
              />
              <PriceCardsMobile
                products={products}
                stores={stores}
                lang={lang}
                accent="#0b6e4f"
                onRefreshPrices={onRefreshPrices}
                refreshing={refreshing}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export function LandingPageDesignBrief() {
  const params = useParams();
  const router = useRouter();
  const pathname = usePathname();
  const urlLang = (ALL_LANGS as string[]).includes(params?.lang as string)
    ? (params.lang as Lang)
    : 'ukr';
  const [lang, setLangState] = useState<Lang>(urlLang);
  useEffect(() => {
    setLangState(urlLang);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlLang]);
  const setLang = useCallback(
    (l: Lang) => {
      const segments = pathname.split('/');
      if (segments.length > 1) {
        segments[1] = l;
        router.push(segments.join('/') || '/');
      }
    },
    [pathname, router]
  );
  const [isProductsOpen, setIsProductsOpen] = useState(false);
  const [isStoresOpen, setIsStoresOpen] = useState(false);
  const [isAboutOpen, setIsAboutOpen] = useState(false);

  // Accounts (Phase 4.2)
  const [currentUser, setCurrentUser] = useState<{ id: string; email: string; tier: string } | null>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Backend Integration (Phase 1)
  const [products, setProducts] = useState(MOCK_PRODUCTS);
  const [stores, setStores] = useState(MOCK_STORES);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Hero search bar - filters the price matrix below by product name
  // (client-side: the full matrix is already loaded, no need to hit the API).
  const [searchQuery, setSearchQuery] = useState('');
  const filteredProducts = products.filter((p: any) =>
    !searchQuery.trim() || (p.name ?? '').toLowerCase().includes(searchQuery.trim().toLowerCase())
  );

  const t = TRANSLATIONS[lang];

  // Fetch price matrix from backend. Page load reads the last persisted scan
  // from MongoDB (fast, no live scrape) - real prices only change once a
  // week via the backend's scheduled Monday 07:00 (Kyiv) job, or on demand
  // via the "Оновити ціни" button, which re-runs the actual cijene.me scrape.
  const fetchMatrix = useCallback(
    async (isManualRefresh = false) => {
      const setBusy = isManualRefresh ? setRefreshing : setLoading;
      try {
        setBusy(true);

        try {
          const response = isManualRefresh
            ? await productsAPI.priceMatrixLive(lang)
            : await productsAPI.matrixCached(lang);
          const data = response.data;

          if (data && data.stores && data.products) {
            setStores(data.stores);
            setProducts(
              data.products.map((p: any) => ({
                id: p.id,
                name: p.name,
                unit: p.unit,
                prices: p.prices,
                imageUrl: p.image_url,
                category: p.category,
              }))
            );
            console.log(`Loaded ${data.products.length} products (${data.source ?? (isManualRefresh ? 'live' : 'cache')})`);
            return;
          }
        } catch (err) {
          console.warn('Primary endpoint failed, falling back to mock:', err);
        }

        // Fallback to old endpoint if the primary call fails
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
        // Keep existing/mock data as fallback
      } finally {
        setBusy(false);
      }
    },
    [lang]
  );

  // Re-fetches whenever the URL locale changes so product names resolve
  // through the new language's `name_i18n` field (Phase 4.6).
  useEffect(() => {
    fetchMatrix();
  }, [fetchMatrix]);

  // Pick up an existing session cookie (e.g. after a magic-link redirect,
  // or a returning visitor) - 401 just means "not logged in", not an error.
  useEffect(() => {
    authAPI
      .me()
      .then((res) => setCurrentUser(res.data))
      .catch(() => setCurrentUser(null));
  }, []);

  const onRefreshPrices = useCallback(() => {
    if (refreshing) return;
    fetchMatrix(true);
  }, [fetchMatrix, refreshing]);

  const onProductsClick = useCallback(() => setIsProductsOpen(true), []);
  const onStoresClick = useCallback(() => setIsStoresOpen(true), []);
  const onAboutClick = useCallback(() => setIsAboutOpen(true), []);
  const onHomeClick = useCallback(() => {
    setIsProductsOpen(false);
    setIsStoresOpen(false);
    setIsAboutOpen(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);
  const onAuthClick = useCallback(() => setIsAuthModalOpen(true), []);
  const onLogoutClick = useCallback(() => {
    authAPI.logout().finally(() => setCurrentUser(null));
  }, []);

  return (
    <>
      <VariationA
        lang={lang}
        setLang={setLang}
        t={t}
        onProductsClick={onProductsClick}
        onStoresClick={onStoresClick}
        onAboutClick={onAboutClick}
        onHomeClick={onHomeClick}
        onRefreshPrices={onRefreshPrices}
        refreshing={refreshing}
        products={filteredProducts}
        stores={stores}
        loading={loading}
        currentUser={currentUser}
        onAuthClick={onAuthClick}
        onLogoutClick={onLogoutClick}
        searchQuery={searchQuery}
        onSearchQueryChange={setSearchQuery}
      />

      {/* Modals */}
      <ShoppingListModal
        isOpen={isProductsOpen}
        onClose={() => setIsProductsOpen(false)}
        products={products}
        lang={lang}
        currentUser={currentUser}
      />
      <StoresModal isOpen={isStoresOpen} onClose={() => setIsStoresOpen(false)} lang={lang} />
      <AboutModal isOpen={isAboutOpen} onClose={() => setIsAboutOpen(false)} lang={lang} />
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthenticated={(user) => setCurrentUser(user)}
        lang={lang}
      />
    </>
  );
}