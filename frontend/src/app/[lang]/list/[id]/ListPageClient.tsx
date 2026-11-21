'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { listsAPI, telegramBotLink } from '@/lib/api';
import { at } from '@/lib/accountText';
import { AuthModal } from '@/components/AuthModal';
import { ShoppingListView, type ShoppingListData } from '@/components/ShoppingListView';
import { ALL_LANGS, type Lang } from '@/lib/productMatrix';

type LoadState = 'loading' | 'ok' | 'notFound' | 'login' | 'forbidden';

export function ListPageClient({ urlLang, listId }: { urlLang: string; listId: string }) {
  const router = useRouter();
  const [data, setData] = useState<ShoppingListData | null>(null);
  const [state, setState] = useState<LoadState>('loading');
  const [authOpen, setAuthOpen] = useState(false);
  // Phase 4.6: the URL locale segment IS the Lang value now, no bridge.
  const lang: Lang = (ALL_LANGS as string[]).includes(urlLang) ? (urlLang as Lang) : 'ukr';

  // Lists are private: 401 = log in first, 403 = this account isn't a member.
  // The list carries its own country and stores - a Ukrainian list must
  // not be drawn against the Montenegrin store columns.
  const load = useCallback(() => {
    listsAPI
      .get(listId, lang)
      .then((res) => {
        setData(res.data);
        setState('ok');
      })
      .catch((err) => {
        const status = err?.response?.status;
        setState(status === 401 ? 'login' : status === 403 ? 'forbidden' : 'notFound');
      });
  }, [listId, lang]);

  useEffect(load, [load]);

  const goHome = () => router.push(`/${urlLang}`);

  return (
    <div className="min-h-screen py-10 px-4" style={{ backgroundColor: '#f5f3f0' }}>
      {state === 'ok' && data ? (
        <ShoppingListView key={`${data.id}-${lang}`} data={data} lang={lang} onBack={goHome} />
      ) : state === 'loading' ? (
        <div className="text-center py-16" style={{ color: '#7d9a8d' }}>
          …
        </div>
      ) : state === 'notFound' ? (
        <div className="text-center py-16" style={{ color: '#7d9a8d' }}>
          {at(lang, 'listNotFound')}
        </div>
      ) : (
        <div className="max-w-[28rem] mx-auto bg-white rounded-2xl shadow-sm p-6 text-center">
          <p className="text-sm mb-2" style={{ color: '#0f3d2e' }}>
            {at(lang, 'listPrivate')}
          </p>
          <p className="text-sm mb-5" style={{ color: '#52736a' }}>
            {at(lang, state === 'login' ? 'listLoginHint' : 'listNoAccess')}
          </p>
          <div className="flex flex-col gap-2">
            {state === 'login' && (
              <button
                onClick={() => setAuthOpen(true)}
                className="w-full py-2.5 rounded-lg font-semibold text-sm"
                style={{ backgroundColor: '#229ED9', color: 'white', border: 'none', cursor: 'pointer' }}
              >
                {at(lang, 'login')}
              </button>
            )}
            <a
              href={telegramBotLink(`list_${listId}`)}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full py-2.5 rounded-lg font-semibold text-sm"
              style={{ backgroundColor: 'white', color: '#229ED9', border: '1px solid #229ED9' }}
            >
              {at(lang, 'openInBot')}
            </a>
            <button
              onClick={goHome}
              className="text-sm mt-1"
              style={{ color: '#52736a', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              {at(lang, 'back')}
            </button>
          </div>
        </div>
      )}
      <AuthModal
        isOpen={authOpen}
        onClose={() => setAuthOpen(false)}
        onAuthenticated={() => {
          setAuthOpen(false);
          setState('loading');
          load();
        }}
        lang={lang}
      />
    </div>
  );
}
