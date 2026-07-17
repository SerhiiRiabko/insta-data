/**
 * SearchBar Component
 * Real-time search with debouncing
 */

'use client';

import { useTranslations } from 'next-intl';
import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';

export function SearchBar() {
  const t = useTranslations();
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const debounceTimer = useRef<NodeJS.Timeout>();

  const handleSearch = useCallback(
    (searchQuery: string) => {
      if (!searchQuery.trim()) return;

      setIsLoading(true);
      // Navigate to search results (will be implemented in next component)
      const params = new URLSearchParams({ q: searchQuery });
      router.push(`?${params.toString()}`);
      setIsLoading(false);
    },
    [router]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);

    // Debounce search
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    if (value.trim()) {
      debounceTimer.current = setTimeout(() => {
        handleSearch(value);
      }, 500);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    handleSearch(query);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-[42rem] mx-auto">
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder={t('search.placeholder')}
            className="input w-full pr-10"
          />
          {isLoading && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <div className="animate-spin w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full" />
            </div>
          )}
        </div>
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="btn btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {t('search.button')}
        </button>
      </div>
    </form>
  );
}