/**
 * TrendingProducts Component
 * Display recently updated products
 */

'use client';

import { useTranslations } from 'next-intl';
import { useState, useEffect } from 'react';
import { ProductCard } from './ProductCard';

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

export function TrendingProducts() {
  const t = useTranslations();
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchTrending();
  }, []);

  const fetchTrending = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      // Try trending first, fallback to mock
      const response = await fetch(`${apiUrl}/api/v1/search/mock?q=`);

      if (response.ok) {
        const data = await response.json();
        setProducts(data.results || []);
      }
    } catch (err) {
      console.error('Error fetching trending:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="grid-cols-responsive">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="skeleton h-80" />
        ))}
      </div>
    );
  }

  if (!products.length) {
    return (
      <div className="text-center py-12">
        <p className="text-neutral-400">{t('noData')}</p>
      </div>
    );
  }

  return (
    <div className="grid-cols-responsive">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}