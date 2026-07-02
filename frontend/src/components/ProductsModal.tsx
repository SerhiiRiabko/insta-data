'use client';

import { useState } from 'react';

interface Product {
  name: string;
  unit: string;
  category?: string;
  prices?: (number | null)[];
}

interface ProductsModalProps {
  isOpen: boolean;
  onClose: () => void;
  products: Product[];
  lang: 'ru' | 'uk' | 'en';
}

const translations = {
  ru: {
    title: 'Товары',
    search: 'Поиск товара...',
    noProducts: 'Товары не найдены',
    category: 'Категория',
    unit: 'Единица',
    addToList: '+ Добавить в список',
  },
  uk: {
    title: 'Товари',
    search: 'Пошук товару...',
    noProducts: 'Товари не знайдені',
    category: 'Категорія',
    unit: 'Одиниця',
    addToList: '+ Додати в список',
  },
  en: {
    title: 'Products',
    search: 'Search products...',
    noProducts: 'No products found',
    category: 'Category',
    unit: 'Unit',
    addToList: '+ Add to list',
  },
};

export function ProductsModal({ isOpen, onClose, products, lang }: ProductsModalProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const t = translations[lang];

  const filteredProducts = products.filter((p) =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  console.log('ProductsModal render:', { isOpen, lang });

  if (!isOpen) return null;
  console.log('ProductsModal rendering modal content');

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[10000] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 p-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">{t.title}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
            aria-label="Close"
          >
            ✕
          </button>
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
        </div>

        {/* Products List */}
        <div className="overflow-y-auto flex-1">
          {filteredProducts.length === 0 ? (
            <div className="flex items-center justify-center h-40 text-gray-500">
              {t.noProducts}
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {filteredProducts.map((product, idx) => (
                <div key={idx} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-2">{product.name}</h3>
                      <div className="text-sm text-gray-600 space-y-1">
                        {product.category && (
                          <p>
                            <span className="font-medium">{t.category}:</span> {product.category}
                          </p>
                        )}
                        <p>
                          <span className="font-medium">{t.unit}:</span> {product.unit}
                        </p>
                      </div>
                    </div>
                    <button className="px-4 py-2 bg-brand-accent text-white rounded-lg hover:bg-brand-deep transition-colors font-semibold text-sm whitespace-nowrap">
                      {t.addToList}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}