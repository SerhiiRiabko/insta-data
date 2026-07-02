/**
 * ProductCard Component - Premium Table Row
 * Single product row with prices and actions
 */

'use client';

import { useState } from 'react';
import Image from 'next/image';

interface ProductCardProps {
  product: {
    id: string;
    name: string;
    description?: string;
    image_url?: string;
    source: string;
    current_prices: Record<string, number>;
    min_price: number;
    cheapest_store?: string;
    updated_at: string;
  };
}

export function ProductCard({ product }: ProductCardProps) {
  const [isWishlisted, setIsWishlisted] = useState(false);

  const getStoreBadge = (store: string) => {
    const badges: Record<string, string> = {
      aroma: '🟦',
      voli: '🟪',
      hdl: '🟧',
      idea: '🟩',
      instagram: '🎵',
    };
    return badges[store] || '📦';
  };

  return (
    <div className="bg-white/5 backdrop-blur-sm hover:bg-white/10 border border-white/10 hover:border-emerald-400/50 rounded-xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-emerald-500/20">
      <div className="flex items-center gap-4">
        {/* Product Image */}
        <div className="flex-shrink-0">
          {product.image_url ? (
            <div className="relative w-16 h-16 rounded-lg overflow-hidden bg-neutral-700">
              <Image
                src={product.image_url}
                alt={product.name}
                fill
                className="object-cover"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.style.display = 'none';
                }}
              />
            </div>
          ) : (
            <div className="w-16 h-16 rounded-lg bg-emerald-900/30 flex items-center justify-center text-2xl">
              📦
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="flex-grow min-w-0">
          <h3 className="font-semibold text-white text-sm line-clamp-1 mb-1">
            {product.name}
          </h3>
          <div className="flex items-center gap-2">
            <span className="text-lg">{getStoreBadge(product.source)}</span>
            <span className="text-xs text-emerald-200 px-2 py-1 bg-emerald-500/20 rounded-full">
              {product.source === 'instagram' ? '📸 Instagram' : product.source.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Prices Grid */}
        <div className="flex-shrink-0 hidden sm:flex gap-3">
          {Object.entries(product.current_prices).map(([store, price]) => (
            <div
              key={store}
              className={`text-center px-3 py-2 rounded-lg transition-all ${
                store === product.cheapest_store
                  ? 'bg-emerald-500/30 border border-emerald-400'
                  : 'bg-white/5 border border-white/10'
              }`}
            >
              <div className="text-xs text-white/70">{store}</div>
              <div className={`font-bold ${store === product.cheapest_store ? 'text-emerald-300' : 'text-emerald-100'}`}>
                €{price.toFixed(2)}
              </div>
            </div>
          ))}
        </div>

        {/* Best Price & Wishlist */}
        <div className="flex-shrink-0 text-right">
          <div className="text-xs text-emerald-200 mb-2">Найдешевше</div>
          <div className="text-xl font-bold text-emerald-300 mb-3">€{product.min_price.toFixed(2)}</div>
          <button
            onClick={() => setIsWishlisted(!isWishlisted)}
            className={`px-3 py-1 rounded-lg text-sm transition-all ${
              isWishlisted
                ? 'bg-emerald-500 text-white hover:bg-emerald-600'
                : 'bg-white/10 text-emerald-200 hover:bg-white/20'
            }`}
          >
            {isWishlisted ? '❤️' : '🤍'}
          </button>
        </div>
      </div>
    </div>
  );
}
