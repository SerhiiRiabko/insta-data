'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { listsAPI } from '@/lib/api';
import { getSessionId, loadCart, saveCart, clearCart, type CartItem } from '@/lib/shoppingCart';
import { groupByCategory, translations as matrixTranslations, type Lang } from '@/lib/productMatrix';

interface Product {
  id?: string;
  name: string;
  unit: string;
  category?: string;
  prices?: (number | null)[];
  imageUrl?: string | null;
}

interface SavedListSummary {
  id: string;
  name: string | null;
  item_count: number;
  updated_at: string;
}

interface ShoppingListModalProps {
  isOpen: boolean;
  onClose: () => void;
  products: Product[];
  lang: Lang;
  currentUser: { id: string; email: string; tier: string } | null;
}

type ShoppingListText = {
  title: string; search: string; noProducts: string; unit: string;
  add: string; added: string; createList: string; creating: string;
  cartEmpty: string; myLists: string; newList: string; unnamed: string;
  itemsCount: (n: number) => string; back: string;
};

const translations: Record<Lang, ShoppingListText> = {
  rus: {
    title: 'Список покупок',
    search: 'Поиск товара...',
    noProducts: 'Товары не найдены',
    unit: 'Единица',
    add: '+ Добавить',
    added: '✓ Добавлено',
    createList: 'Создать список',
    creating: 'Создаём…',
    cartEmpty: 'Добавьте товары, чтобы создать список',
    myLists: 'Мои списки',
    newList: '+ Новый список',
    unnamed: 'Без названия',
    itemsCount: (n: number) => `${n} товар(ов)`,
    back: '← Мои списки',
  },
  ukr: {
    title: 'Список покупок',
    search: 'Пошук товару...',
    noProducts: 'Товари не знайдені',
    unit: 'Одиниця',
    add: '+ Додати',
    added: '✓ Додано',
    createList: 'Створити список',
    creating: 'Створюємо…',
    cartEmpty: 'Додайте товари, щоб створити список',
    myLists: 'Мої списки',
    newList: '+ Новий список',
    unnamed: 'Без назви',
    itemsCount: (n: number) => `${n} товар(ів)`,
    back: '← Мої списки',
  },
  eng: {
    title: 'Shopping list',
    search: 'Search products...',
    noProducts: 'No products found',
    unit: 'Unit',
    add: '+ Add',
    added: '✓ Added',
    createList: 'Create list',
    creating: 'Creating…',
    cartEmpty: 'Add products to create a list',
    myLists: 'My lists',
    newList: '+ New list',
    unnamed: 'Untitled',
    itemsCount: (n: number) => `${n} item(s)`,
    back: '← My lists',
  },
  mne: {
    title: 'Lista za kupovinu',
    search: 'Pretraga proizvoda...',
    noProducts: 'Proizvodi nisu pronađeni',
    unit: 'Jedinica',
    add: '+ Dodaj',
    added: '✓ Dodato',
    createList: 'Kreiraj listu',
    creating: 'Kreiramo…',
    cartEmpty: 'Dodajte proizvode da kreirate listu',
    myLists: 'Moje liste',
    newList: '+ Nova lista',
    unnamed: 'Bez naziva',
    itemsCount: (n: number) => `${n} proizvod(a)`,
    back: '← Moje liste',
  },
  srb: {
    title: 'Lista za kupovinu',
    search: 'Pretraga proizvoda...',
    noProducts: 'Proizvodi nisu pronađeni',
    unit: 'Jedinica',
    add: '+ Dodaj',
    added: '✓ Dodato',
    createList: 'Kreiraj listu',
    creating: 'Kreiramo…',
    cartEmpty: 'Dodajte proizvode da kreirate listu',
    myLists: 'Moje liste',
    newList: '+ Nova lista',
    unnamed: 'Bez naziva',
    itemsCount: (n: number) => `${n} proizvod(a)`,
    back: '← Moje liste',
  },
  bos: {
    title: 'Lista za kupovinu',
    search: 'Pretraga proizvoda...',
    noProducts: 'Proizvodi nisu pronađeni',
    unit: 'Jedinica',
    add: '+ Dodaj',
    added: '✓ Dodato',
    createList: 'Kreiraj listu',
    creating: 'Kreiramo…',
    cartEmpty: 'Dodajte proizvode da kreirate listu',
    myLists: 'Moje liste',
    newList: '+ Nova lista',
    unnamed: 'Bez naziva',
    itemsCount: (n: number) => `${n} proizvod(a)`,
    back: '← Moje liste',
  },
};

export function ShoppingListModal({ isOpen, onClose, products, lang, currentUser }: ShoppingListModalProps) {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState('');
  const [cart, setCart] = useState<CartItem[]>([]);
  const [creating, setCreating] = useState(false);
  const [view, setView] = useState<'myLists' | 'builder'>('builder');
  const [myLists, setMyLists] = useState<SavedListSummary[] | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const t = translations[lang];

  useEffect(() => {
    if (isOpen) setCart(loadCart());
  }, [isOpen]);

  // Logged-in users with at least one saved list land on "My lists" first;
  // guests (and logged-in users with none yet) go straight to the builder.
  useEffect(() => {
    if (!isOpen) return;
    if (!currentUser) {
      setView('builder');
      setMyLists(null);
      return;
    }
    listsAPI
      .mine()
      .then((res) => {
        const lists: SavedListSummary[] = res.data.lists;
        setMyLists(lists);
        setView(lists.length > 0 ? 'myLists' : 'builder');
      })
      .catch(() => setView('builder'));
  }, [isOpen, currentUser]);

  // Category grouping is derived client-side from the `products` prop - the
  // same already-cached matrix data the landing page shows, not a fresh
  // fetch. This used to call GET /products/by-category on every modal open,
  // which re-ran the full ~10-15s live cijene.me scrape (and, under React 18
  // StrictMode's double-effect-invoke in dev, fired it twice concurrently) -
  // slow, and a live external scrape occasionally coming back empty/flaky
  // left the modal permanently stuck on "no products found" with no
  // fallback. Grouping what's already loaded is instant and can't fail.
  const otherLabel = matrixTranslations[lang].other;
  const groups = useMemo(() => groupByCategory(products, otherLabel), [products, otherLabel]);

  if (!isOpen) return null;

  const search = searchTerm.toLowerCase();
  const matches = (name: string) => name.toLowerCase().includes(search);

  const filteredCategories = groups
    .map((cat) => ({ ...cat, rows: cat.rows.filter((p) => matches(p.name)) }))
    .filter((cat) => cat.rows.length > 0);

  const isEmpty = filteredCategories.length === 0;

  const inCart = (id?: string) => !!id && cart.some((c) => c.product_id === id);

  const toggleCart = (product: Product) => {
    if (!product.id) return;
    setCart((prev) => {
      const next = inCart(product.id)
        ? prev.filter((c) => c.product_id !== product.id)
        : [...prev, { product_id: product.id!, name: product.name, unit: product.unit }];
      saveCart(next);
      return next;
    });
  };

  const goToList = (id: string) => {
    // Navigate first, then close - closing the modal unmounts it (and its
    // `router` closure) synchronously, which can race a router.push issued
    // right after and drop the navigation. `lang` IS the URL locale segment
    // now (Phase 4.6 unification), no bridge needed.
    router.push(`/${lang}/list/${id}`);
    onClose();
  };

  const createList = async () => {
    if (cart.length === 0 || creating) return;
    setCreating(true);
    setCreateError(null);
    try {
      const sessionId = getSessionId();
      const response = await listsAPI.create(cart, sessionId);
      clearCart();
      goToList(response.data.id);
    } catch (err: any) {
      console.error('Failed to create list:', err);
      setCreateError(err?.response?.data?.detail || 'Failed to create list.');
      setCreating(false);
    }
  };

  if (view === 'myLists') {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[10000] flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl max-w-[42rem] w-full max-h-[80vh] flex flex-col">
          <div className="border-b border-gray-200 p-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">{t.myLists}</h2>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setView('builder')}
                className="px-4 py-2 rounded-lg font-semibold text-sm whitespace-nowrap"
                style={{ backgroundColor: '#0b6e4f', color: 'white', border: 'none', cursor: 'pointer' }}
              >
                {t.newList}
              </button>
              <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl" aria-label="Close">
                ✕
              </button>
            </div>
          </div>
          <div className="overflow-y-auto flex-1 divide-y divide-gray-100">
            {(myLists ?? []).map((list) => (
              <button
                key={list.id}
                onClick={() => goToList(list.id)}
                className="w-full text-left p-6 hover:bg-gray-50 transition-colors flex items-center justify-between"
              >
                <span className="font-semibold text-gray-900">{list.name || t.unnamed}</span>
                <span className="text-sm text-gray-500">{t.itemsCount(list.item_count)}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[10000] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-[42rem] w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 p-6 flex items-center justify-between">
          <div>
            {myLists !== null && myLists.length > 0 && (
              <button
                onClick={() => setView('myLists')}
                className="block text-xs font-medium mb-1"
                style={{ color: '#52736a', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                {t.back}
              </button>
            )}
            <h2 className="text-2xl font-bold text-gray-900">{t.title}</h2>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={createList}
              disabled={cart.length === 0 || creating}
              title={cart.length === 0 ? t.cartEmpty : undefined}
              className="px-4 py-2 rounded-lg font-semibold text-sm whitespace-nowrap"
              style={{
                backgroundColor: cart.length === 0 ? '#e3eee8' : '#0b6e4f',
                color: cart.length === 0 ? '#a3b5ae' : 'white',
                border: 'none',
                cursor: cart.length === 0 || creating ? 'default' : 'pointer',
              }}
            >
              {creating ? t.creating : `${t.createList}${cart.length > 0 ? ` (${cart.length})` : ''}`}
            </button>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
              aria-label="Close"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="px-6 py-4 border-b border-gray-100">
          <input
            type="text"
            placeholder={t.search}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-accent"
          />
          {createError && <p className="text-sm text-red-600 mt-2">{createError}</p>}
        </div>

        {/* Products List */}
        <div className="overflow-y-auto flex-1">
          {isEmpty ? (
            <div className="flex items-center justify-center h-40 text-gray-500">
              {t.noProducts}
            </div>
          ) : (
            filteredCategories.map((cat) => (
              <div key={cat.name}>
                <div className="sticky top-0 bg-gray-50 px-6 py-2 text-sm font-bold text-gray-700 border-y border-gray-200">
                  {cat.name} ({cat.rows.length})
                </div>
                <div className="divide-y divide-gray-100">
                  {cat.rows.map((product, idx) => (
                    <ProductRow
                      key={idx}
                      product={product}
                      unitLabel={t.unit}
                      addLabel={t.add}
                      addedLabel={t.added}
                      inCart={inCart(product.id)}
                      onToggle={() => toggleCart(product)}
                    />
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function ProductRow({
  product,
  unitLabel,
  addLabel,
  addedLabel,
  inCart,
  onToggle,
}: {
  product: Product;
  unitLabel: string;
  addLabel: string;
  addedLabel: string;
  inCart: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="p-6 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          {product.imageUrl && (
            <img
              src={product.imageUrl}
              alt=""
              className="w-7 h-7 rounded object-cover flex-shrink-0 mt-0.5"
            />
          )}
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 mb-2">{product.name}</h3>
            <div className="text-sm text-gray-600 space-y-1">
              <p>
                <span className="font-medium">{unitLabel}:</span> {product.unit}
              </p>
            </div>
          </div>
        </div>
        <button
          onClick={onToggle}
          disabled={!product.id}
          className="px-4 py-2 rounded-lg font-semibold text-sm whitespace-nowrap transition-colors"
          style={{
            backgroundColor: inCart ? '#d8f3e3' : '#0b6e4f',
            color: inCart ? '#05603a' : 'white',
            border: 'none',
            cursor: product.id ? 'pointer' : 'default',
            opacity: product.id ? 1 : 0.5,
          }}
        >
          {inCart ? addedLabel : addLabel}
        </button>
      </div>
    </div>
  );
}
