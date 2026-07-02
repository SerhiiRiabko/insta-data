/**
 * PriceMatrix Component
 * Display products in grid with prices per store
 */

'use client';

import { useTranslations } from 'next-intl';
import { useState, useEffect } from 'react';
import { ProductCard } from './ProductCard';
import { useSearchParams } from 'next/navigation';

interface Product {
  id: string;
  name: string;
  description?: string;
  image_url?: string;
  source: string;
  current_prices: Record<string, number>;
  min_price: number;
  cheapest_store?: string;
  updated_at: string;
}

export function PriceMatrix() {
  const t = useTranslations();
  const searchParams = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const query = searchParams.get('q');
    if (query) {
      fetchProducts(query);
    }
  }, [searchParams]);

  const fetchProducts = async (query: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const response = await fetch(`${apiUrl}/api/v1/search/products?q=${encodeURIComponent(query)}`);

      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();
      setProducts(data.results || []);

      if (data.results.length === 0) {
        setError(t('search.noResults'));
      }
    } catch (err) {
      setError(t('errors.search'));
      console.error('Search error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-neutral-400">{t('loading')}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6 text-center">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-neutral-400 text-lg">{t('noData')}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4 text-sm text-neutral-400">
        {t('search.results')}: <span className="font-semibold text-neutral-50">{products.length}</span>
      </div>

      <div className="grid-cols-responsive">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  );
}