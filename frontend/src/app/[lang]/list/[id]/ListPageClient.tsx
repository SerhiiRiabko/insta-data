'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { listsAPI } from '@/lib/api';
import { ShoppingListView, type ShoppingListData } from '@/components/ShoppingListView';
import { DEFAULT_STORES, ALL_LANGS, type Lang } from '@/lib/productMatrix';

export function ListPageClient({ urlLang, listId }: { urlLang: string; listId: string }) {
  const router = useRouter();
  const [data, setData] = useState<ShoppingListData | null>(null);
  const [notFound, setNotFound] = useState(false);
  // Phase 4.6: the URL locale segment IS the Lang value now, no bridge.
  const lang: Lang = (ALL_LANGS as string[]).includes(urlLang) ? (urlLang as Lang) : 'ukr';

  useEffect(() => {
    listsAPI
      .get(listId)
      .then((res) => setData(res.data))
      .catch(() => setNotFound(true));
  }, [listId]);

  return (
    <div className="min-h-screen py-10 px-4" style={{ backgroundColor: '#f5f3f0' }}>
      {notFound ? (
        <div className="text-center py-16" style={{ color: '#7d9a8d' }}>
          List not found.
        </div>
      ) : !data ? (
        <div className="text-center py-16" style={{ color: '#7d9a8d' }}>
          …
        </div>
      ) : (
        <ShoppingListView
          data={data}
          stores={DEFAULT_STORES}
          lang={lang}
          onBack={() => router.push(`/${urlLang}`)}
        />
      )}
    </div>
  );
}
