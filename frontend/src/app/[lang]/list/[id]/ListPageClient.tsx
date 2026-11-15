'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { listsAPI } from '@/lib/api';
import { ShoppingListView, type ShoppingListData } from '@/components/ShoppingListView';
import { ALL_LANGS, type Lang } from '@/lib/productMatrix';

export function ListPageClient({ urlLang, listId }: { urlLang: string; listId: string }) {
  const router = useRouter();
  const [data, setData] = useState<ShoppingListData | null>(null);
  const [notFound, setNotFound] = useState(false);
  // Phase 4.6: the URL locale segment IS the Lang value now, no bridge.
  const lang: Lang = (ALL_LANGS as string[]).includes(urlLang) ? (urlLang as Lang) : 'ukr';

  // The list carries its own country and stores - a Ukrainian list must
  // not be drawn against the Montenegrin store columns.
  useEffect(() => {
    listsAPI
      .get(listId, lang)
      .then((res) => setData(res.data))
      .catch(() => setNotFound(true));
  }, [listId, lang]);

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
        <ShoppingListView key={`${data.id}-${lang}`} data={data} lang={lang} onBack={() => router.push(`/${urlLang}`)} />
      )}
    </div>
  );
}
