'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { authAPI, listsAPI, telegramBotLink, TELEGRAM_BOT_USERNAME, type Country, type CurrentUser } from '@/lib/api';
import { at } from '@/lib/accountText';
import { useProductSearch } from '@/lib/useProductSearch';
import { formatPrice, type MatrixStore, type Lang } from '@/lib/productMatrix';

export interface ShoppingListItem {
  product_id: string;
  name: string;
  unit: string;
  checked: boolean;
  prices: (number | null)[];
  min_price: number | null;
  cheapest_store: string | null;
}

export interface ShoppingListData {
  id: string;
  name: string | null;
  saved: boolean;
  owner_user_id: string | null;
  // The list's own country and its stores, in the same column order as
  // each item's `prices`.
  country: Country;
  stores: MatrixStore[];
  items: ShoppingListItem[];
  total_cheapest: number;
  created_at: string;
  updated_at: string;
  // Who's looking: owner | member | admin | guest (legacy ownerless list).
  role: 'owner' | 'member' | 'admin' | 'guest' | null;
  can_edit: boolean;
  owner_name: string | null;
  members: { id: string; name: string }[]; // owner only
}

type ShoppingListText = {
  title: string; empty: string; cheapestAt: string;
  back: string; itemsCount: (n: number) => string; save: string; saving: string;
  saved: string; namePlaceholder: string; confirm: string; cancel: string;
};

const translations: Record<Lang, ShoppingListText> = {
  rus: {
    title: 'Список покупок',
    empty: 'Список пуст',
    cheapestAt: 'Дешевле всего в',
    back: 'На главную',
    itemsCount: (n: number) => `${n} товар(ов)`,
    save: 'Сохранить список',
    saving: 'Сохраняем…',
    saved: '✓ Сохранено',
    namePlaceholder: 'Название списка',
    confirm: 'Сохранить',
    cancel: 'Отмена',
  },
  ukr: {
    title: 'Список покупок',
    empty: 'Список порожній',
    cheapestAt: 'Найдешевше в',
    back: 'На головну',
    itemsCount: (n: number) => `${n} товар(ів)`,
    save: 'Зберегти список',
    saving: 'Зберігаємо…',
    saved: '✓ Збережено',
    namePlaceholder: 'Назва списку',
    confirm: 'Зберегти',
    cancel: 'Скасувати',
  },
  eng: {
    title: 'Shopping list',
    empty: 'List is empty',
    cheapestAt: 'Cheapest at',
    back: 'Home',
    itemsCount: (n: number) => `${n} item(s)`,
    save: 'Save list',
    saving: 'Saving…',
    saved: '✓ Saved',
    namePlaceholder: 'List name',
    confirm: 'Save',
    cancel: 'Cancel',
  },
  mne: {
    title: 'Lista za kupovinu',
    empty: 'Lista je prazna',
    cheapestAt: 'Najjeftinije u',
    back: 'Početna',
    itemsCount: (n: number) => `${n} proizvod(a)`,
    save: 'Sačuvaj listu',
    saving: 'Čuvamo…',
    saved: '✓ Sačuvano',
    namePlaceholder: 'Naziv liste',
    confirm: 'Sačuvaj',
    cancel: 'Otkaži',
  },
  srb: {
    title: 'Lista za kupovinu',
    empty: 'Lista je prazna',
    cheapestAt: 'Najjeftinije u',
    back: 'Početna',
    itemsCount: (n: number) => `${n} proizvod(a)`,
    save: 'Sačuvaj listu',
    saving: 'Čuvamo…',
    saved: '✓ Sačuvano',
    namePlaceholder: 'Naziv liste',
    confirm: 'Sačuvaj',
    cancel: 'Otkaži',
  },
  bos: {
    title: 'Lista za kupovinu',
    empty: 'Lista je prazna',
    cheapestAt: 'Najjeftinije u',
    back: 'Početna',
    itemsCount: (n: number) => `${n} proizvod(a)`,
    save: 'Sačuvaj listu',
    saving: 'Čuvamo…',
    saved: '✓ Sačuvano',
    namePlaceholder: 'Naziv liste',
    confirm: 'Sačuvaj',
    cancel: 'Otkaži',
  },
};

// Changes made in the bot (ticks, items added by other members) appear
// without a reload.
const SYNC_INTERVAL_MS = 15000;

interface ShoppingListViewProps {
  data: ShoppingListData;
  lang: Lang;
  accent?: string;
  onBack?: () => void;
}

export function ShoppingListView({ data, lang, accent = '#0b6e4f', onBack }: ShoppingListViewProps) {
  const t = translations[lang];
  const [list, setList] = useState<ShoppingListData>(data);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [copied, setCopied] = useState(false);
  const [namingOpen, setNamingOpen] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [recipient, setRecipient] = useState('');
  const [sendState, setSendState] = useState<'idle' | 'sending' | 'sent' | 'notFound' | 'error'>('idle');
  const [inviting, setInviting] = useState(false);
  const [addQuery, setAddQuery] = useState('');
  const [error, setError] = useState<string | null>(null);
  const busy = useRef(0); // in-flight writes: skip background sync meanwhile

  const { results: addResults, loading: addLoading } = useProductSearch(addQuery, list.country, lang);

  useEffect(() => {
    authAPI
      .me()
      .then((res) => setCurrentUser(res.data))
      .catch(() => setCurrentUser(null));
  }, []);

  const role = list.role;
  const isOwner = role === 'owner';
  const isMember = role === 'member';
  const isGold = !!currentUser?.access.lists;
  const stores: MatrixStore[] = list.stores;
  const items = list.items;
  const cheapestTotal = items
    .filter((i) => !i.checked && i.min_price !== null)
    .reduce((sum, i) => sum + (i.min_price as number), 0);

  const write = useCallback(async (fn: () => Promise<{ data: ShoppingListData }>, onError?: () => void) => {
    busy.current += 1;
    setError(null);
    try {
      const res = await fn();
      setList(res.data);
    } catch (err) {
      console.error('List update failed:', err);
      setError(at(lang, 'error'));
      onError?.();
    } finally {
      busy.current -= 1;
    }
  }, [lang]);

  // Background sync with whatever happened in Telegram.
  useEffect(() => {
    const timer = setInterval(() => {
      if (document.visibilityState !== 'visible' || busy.current > 0) return;
      listsAPI
        .get(list.id, lang)
        .then((res) => busy.current === 0 && setList(res.data))
        .catch(() => undefined);
    }, SYNC_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [list.id, lang]);

  const toggle = (productId: string) => {
    const flip = () =>
      setList((prev) => ({
        ...prev,
        items: prev.items.map((i) => (i.product_id === productId ? { ...i, checked: !i.checked } : i)),
      }));
    flip(); // optimistic
    write(() => listsAPI.toggleItem(list.id, productId, lang), flip);
  };

  const addProduct = (product: { id: string; name: string; unit: string }) =>
    write(() => listsAPI.addItems(list.id, [{ product_id: product.id, name: product.name, unit: product.unit }], lang));

  const removeProduct = (productId: string) => write(() => listsAPI.removeItem(list.id, productId, lang));

  const removeMember = (userId: string) => write(() => listsAPI.removeMember(list.id, userId, lang));

  const leave = async () => {
    if (!currentUser) return;
    try {
      await listsAPI.removeMember(list.id, currentUser.id, lang);
      onBack?.();
    } catch {
      setError(at(lang, 'error'));
    }
  };

  const inviteViaTelegram = async () => {
    if (inviting) return;
    setInviting(true);
    // Open the tab synchronously (popup blockers), then point it at the share URL.
    const tab = window.open('', '_blank');
    try {
      const res = await listsAPI.invite(list.id);
      const text = at(lang, 'shareMessage');
      const url = `https://t.me/share/url?url=${encodeURIComponent(res.data.url)}&text=${encodeURIComponent(text)}`;
      if (tab) tab.location.href = url;
      else window.open(url, '_blank', 'noopener,noreferrer');
    } catch {
      tab?.close();
      setError(at(lang, 'error'));
    } finally {
      setInviting(false);
    }
  };

  const sendToUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!recipient.trim()) return;
    setSendState('sending');
    try {
      const res = await listsAPI.addMember(list.id, recipient.trim(), lang);
      setList(res.data);
      setSendState('sent');
      setRecipient('');
    } catch (err: any) {
      setSendState(err?.response?.data?.detail === 'telegram_user_not_found' ? 'notFound' : 'error');
    }
  };

  const confirmSave = async () => {
    if (!nameInput.trim() || saving) return;
    setSaving(true);
    setSaveError(null);
    try {
      const response = await listsAPI.save(list.id, nameInput.trim(), lang);
      setList(response.data);
      setNamingOpen(false);
    } catch (err: any) {
      console.error('Failed to save list:', err);
      setSaveError(err?.response?.data?.detail || 'Failed to save list.');
    } finally {
      setSaving(false);
    }
  };

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy link:', err);
    }
  };

  const inList = new Set(items.map((i) => i.product_id));
  const pill = { padding: '8px 16px', borderRadius: 9999, fontSize: 14, fontWeight: 600, cursor: 'pointer' } as const;

  return (
    <div className="w-full max-w-[42rem] mx-auto" style={{ fontFamily: 'inherit' }}>
      <div className="flex items-center justify-between mb-4 px-1 gap-3 flex-wrap">
        <div className="min-w-0">
          <h1 className="text-xl font-bold" style={{ color: '#0f3d2e' }}>
            {list.name || t.title}
          </h1>
          <p className="text-sm" style={{ color: '#7d9a8d' }}>
            {t.itemsCount(items.length)}
            {cheapestTotal > 0 && ` · ${at(lang, 'cheapestTotal')}: ${formatPrice(cheapestTotal, lang, list.country)}`}
          </p>
          {isMember && list.owner_name && (
            <p className="text-xs mt-0.5" style={{ color: '#52736a' }}>
              👥 {at(lang, 'sharedBy', { owner: list.owner_name })}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {onBack && (
            <button
              onClick={onBack}
              className="text-sm font-medium"
              style={{ color: '#52736a', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              {t.back}
            </button>
          )}
          {role === 'guest' && isGold && !list.saved && (
            <button
              onClick={() => setNamingOpen(true)}
              style={{ ...pill, backgroundColor: 'white', color: accent, border: `1px solid ${accent}` }}
            >
              {t.save}
            </button>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 mb-4 px-1 flex-wrap">
        {isOwner && isGold && (
          <button
            onClick={inviteViaTelegram}
            disabled={inviting}
            title={at(lang, 'inviteHint')}
            style={{ ...pill, backgroundColor: '#229ED9', color: 'white', border: 'none' }}
          >
            ✈️ {at(lang, 'inviteTelegram')}
          </button>
        )}
        {role !== 'guest' && (
          <a
            href={telegramBotLink(`list_${list.id}`)}
            target="_blank"
            rel="noopener noreferrer"
            style={{ ...pill, backgroundColor: 'white', color: '#229ED9', border: '1px solid #229ED9' }}
          >
            {at(lang, 'openInBot')}
          </a>
        )}
        <button
          onClick={copyLink}
          style={{
            ...pill,
            backgroundColor: copied ? '#d8f3e3' : 'white',
            color: copied ? '#05603a' : '#52736a',
            border: `1px solid ${copied ? '#d8f3e3' : '#d0d9d5'}`,
          }}
        >
          {copied ? at(lang, 'linkCopied') : at(lang, 'copyLink')}
        </button>
        {isMember && (
          <button
            onClick={leave}
            style={{ ...pill, backgroundColor: 'white', color: '#b42318', border: '1px solid #f3c3bd' }}
          >
            {at(lang, 'leaveList')}
          </button>
        )}
      </div>

      {isOwner && isGold && (
        <div className="mb-4 px-1">
          <form onSubmit={sendToUser}>
            <label className="block text-xs font-medium mb-1" style={{ color: '#52736a' }}>
              {at(lang, 'addMemberLabel')}
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={recipient}
                onChange={(e) => {
                  setRecipient(e.target.value);
                  if (sendState !== 'sending') setSendState('idle');
                }}
                placeholder="@username"
                className="flex-1 min-w-0 px-3 py-2 border rounded-lg text-sm"
                style={{ borderColor: '#d0d9d5' }}
              />
              <button
                type="submit"
                disabled={!recipient.trim() || sendState === 'sending'}
                className="px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap"
                style={{ backgroundColor: '#229ED9', color: 'white', border: 'none', cursor: 'pointer' }}
              >
                {at(lang, 'send')}
              </button>
            </div>
            {sendState === 'sent' && <p className="text-xs mt-2" style={{ color: '#05603a' }}>{at(lang, 'memberAdded')}</p>}
            {sendState === 'notFound' && (
              <p className="text-xs mt-2" style={{ color: '#b45309' }}>
                {at(lang, 'userNotFound', { bot: TELEGRAM_BOT_USERNAME })}
              </p>
            )}
            {sendState === 'error' && <p className="text-xs mt-2 text-red-600">{at(lang, 'error')}</p>}
          </form>

          <div className="mt-3">
            <div className="text-xs font-medium mb-1" style={{ color: '#52736a' }}>
              👥 {at(lang, 'members')}
            </div>
            {list.members.length === 0 ? (
              <p className="text-xs" style={{ color: '#a3b5ae' }}>{at(lang, 'noMembers')}</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {list.members.map((m) => (
                  <span
                    key={m.id}
                    className="inline-flex items-center gap-1 text-xs rounded-full"
                    style={{ padding: '4px 6px 4px 10px', backgroundColor: '#eef5f1', color: '#0f3d2e' }}
                  >
                    {m.name}
                    <button
                      onClick={() => removeMember(m.id)}
                      aria-label={at(lang, 'remove')}
                      title={at(lang, 'remove')}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#7d9a8d', padding: '0 4px' }}
                    >
                      ✕
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {namingOpen && (
        <div className="mb-4 px-1">
          <div className="flex items-center gap-2">
            <input
              type="text"
              autoFocus
              placeholder={t.namePlaceholder}
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && confirmSave()}
              className="flex-1 min-w-0 px-3 py-2 border rounded-lg text-sm"
              style={{ borderColor: '#d0d9d5' }}
            />
            <button
              onClick={confirmSave}
              disabled={!nameInput.trim() || saving}
              className="px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap"
              style={{ backgroundColor: accent, color: 'white', border: 'none', cursor: 'pointer' }}
            >
              {saving ? t.saving : t.confirm}
            </button>
            <button
              onClick={() => setNamingOpen(false)}
              className="px-3 py-2 text-sm"
              style={{ color: '#52736a', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              {t.cancel}
            </button>
          </div>
          {saveError && <p className="text-sm text-red-600 mt-2">{saveError}</p>}
        </div>
      )}

      {list.can_edit ? (
        <div className="mb-4 px-1">
          <input
            type="text"
            value={addQuery}
            onChange={(e) => setAddQuery(e.target.value)}
            placeholder={`＋ ${at(lang, 'addSearchPlaceholder')}`}
            aria-label={at(lang, 'addProducts')}
            className="w-full px-3 py-2 border rounded-lg text-sm"
            style={{ borderColor: '#d0d9d5', backgroundColor: 'white' }}
          />
          {addQuery.trim().length >= 2 && (
            <div className="mt-1 bg-white rounded-lg border overflow-hidden" style={{ borderColor: '#e3eee8' }}>
              {addLoading && !addResults ? (
                <div className="px-3 py-2 text-sm" style={{ color: '#7d9a8d' }}>{at(lang, 'searching')}</div>
              ) : !addResults || addResults.length === 0 ? (
                <div className="px-3 py-2 text-sm" style={{ color: '#7d9a8d' }}>{at(lang, 'nothingFound')}</div>
              ) : (
                addResults.slice(0, 8).map((r, idx) => (
                  <div
                    key={r.id}
                    className="flex items-center justify-between gap-3 px-3 py-2"
                    style={{ borderTop: idx > 0 ? '1px solid #f0f0f0' : 'none' }}
                  >
                    <div className="min-w-0">
                      <div className="text-sm truncate" style={{ color: '#0f1419' }}>{r.name}</div>
                      {r.unit && <div className="text-xs" style={{ color: '#a3b5ae' }}>{r.unit}</div>}
                    </div>
                    {inList.has(r.id) ? (
                      <span className="text-xs whitespace-nowrap" style={{ color: '#05603a' }}>{at(lang, 'inList')}</span>
                    ) : (
                      <button
                        onClick={() => addProduct(r)}
                        className="px-3 py-1 rounded-lg text-xs font-semibold whitespace-nowrap"
                        style={{ backgroundColor: accent, color: 'white', border: 'none', cursor: 'pointer' }}
                      >
                        ＋
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      ) : (
        isMember && <p className="mb-4 px-1 text-xs" style={{ color: '#b45309' }}>{at(lang, 'readOnly')}</p>
      )}

      {error && <p className="mb-3 px-1 text-sm text-red-600">{error}</p>}

      {items.length === 0 ? (
        <div className="text-center py-16" style={{ color: '#7d9a8d' }}>
          {t.empty}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border overflow-hidden" style={{ borderColor: '#e3eee8' }}>
          {items.map((item, idx) => (
            <div
              key={item.product_id}
              className="px-4 py-3"
              style={{ borderTop: idx > 0 ? '1px solid #f0f0f0' : 'none' }}
            >
              <div className="flex items-center gap-3">
                <button
                  onClick={() => toggle(item.product_id)}
                  aria-label={item.checked ? 'uncheck' : 'check'}
                  style={{
                    width: '22px',
                    height: '22px',
                    borderRadius: '6px',
                    border: `2px solid ${item.checked ? accent : '#d0d9d5'}`,
                    backgroundColor: item.checked ? accent : 'white',
                    color: 'white',
                    fontSize: '13px',
                    lineHeight: 1,
                    cursor: 'pointer',
                    flexShrink: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {item.checked ? '✓' : ''}
                </button>

                <div className="flex-1 min-w-0">
                  <div
                    className="font-medium text-sm truncate"
                    style={{
                      color: item.checked ? '#a3b5ae' : '#0f1419',
                      textDecoration: item.checked ? 'line-through' : 'none',
                    }}
                  >
                    {item.name}
                  </div>
                  <div className="text-xs" style={{ color: '#a3b5ae' }}>
                    {item.unit}
                  </div>
                </div>

                <div className="text-right flex-shrink-0">
                  <div
                    className="text-sm font-bold"
                    style={{
                      color: item.checked ? '#a3b5ae' : accent,
                      fontFamily: 'Space Grotesk, monospace',
                    }}
                  >
                    {formatPrice(item.min_price, lang, list.country)}
                  </div>
                  {item.cheapest_store && (
                    <div className="text-[10px]" style={{ color: '#a3b5ae' }}>
                      {t.cheapestAt} {item.cheapest_store}
                    </div>
                  )}
                </div>

                {list.can_edit && (
                  <button
                    onClick={() => removeProduct(item.product_id)}
                    aria-label={at(lang, 'remove')}
                    title={at(lang, 'remove')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#c4d1cb', fontSize: 14, padding: '0 2px', flexShrink: 0 }}
                  >
                    ✕
                  </button>
                )}
              </div>

              {/* Prices by store, so a shared list also shows where each item is cheapest */}
              {!item.checked && (
                <div className="flex gap-1 mt-2 pl-8">
                  {stores.map((store, i) => {
                    const price = item.prices[i];
                    const isCheapest = store.name === item.cheapest_store && price !== null;
                    return (
                      <div
                        key={store.name}
                        className="flex-1 text-center rounded"
                        style={{
                          padding: '3px 2px',
                          backgroundColor: isCheapest ? '#d8f3e3' : '#f7f5f0',
                        }}
                      >
                        <div
                          className="text-[9px] font-semibold"
                          style={{ color: isCheapest ? '#05603a' : '#a3b5ae' }}
                        >
                          {store.initial}
                        </div>
                        <div
                          className="text-[10px]"
                          style={{
                            fontFamily: 'Space Grotesk, monospace',
                            fontWeight: isCheapest ? 700 : 400,
                            color: price === null ? '#ccc' : isCheapest ? '#05603a' : '#52736a',
                          }}
                        >
                          {price === null ? '—' : formatPrice(price, lang, list.country)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {role !== 'guest' && (
        <p className="text-[11px] text-center mt-3" style={{ color: '#a3b5ae' }}>
          {at(lang, 'syncHint')}
        </p>
      )}
    </div>
  );
}
