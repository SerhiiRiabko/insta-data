'use client';

import { useEffect, useState } from 'react';
import { authAPI, listsAPI, telegramBotLink, TELEGRAM_BOT_USERNAME, type Country, type CurrentUser } from '@/lib/api';
import { at } from '@/lib/accountText';
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
}

type ShoppingListText = {
  title: string; empty: string; cheapestAt: string; share: string; copied: string;
  back: string; itemsCount: (n: number) => string; save: string; saving: string;
  saved: string; namePlaceholder: string; confirm: string; cancel: string;
};

const translations: Record<Lang, ShoppingListText> = {
  rus: {
    title: 'Список покупок',
    empty: 'Список пуст',
    cheapestAt: 'Дешевле всего в',
    share: 'Поделиться списком',
    copied: 'Ссылка скопирована!',
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
    share: 'Поділитися списком',
    copied: 'Посилання скопійовано!',
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
    share: 'Share list',
    copied: 'Link copied!',
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
    share: 'Podijeli listu',
    copied: 'Link kopiran!',
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
    share: 'Podeli listu',
    copied: 'Link kopiran!',
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
    share: 'Podijeli listu',
    copied: 'Link kopiran!',
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

interface ShoppingListViewProps {
  data: ShoppingListData;
  lang: Lang;
  accent?: string;
  onBack?: () => void;
}

export function ShoppingListView({ data, lang, accent = '#0b6e4f', onBack }: ShoppingListViewProps) {
  const t = translations[lang];
  const stores: MatrixStore[] = data.stores;
  const [items, setItems] = useState(data.items);
  const [copied, setCopied] = useState(false);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [saved, setSaved] = useState(data.saved);
  const [listName, setListName] = useState(data.name);
  const [namingOpen, setNamingOpen] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [recipient, setRecipient] = useState('');
  const [sendState, setSendState] = useState<'idle' | 'sending' | 'sent' | 'notFound' | 'error'>('idle');

  useEffect(() => {
    authAPI
      .me()
      .then((res) => setCurrentUser(res.data))
      .catch(() => setCurrentUser(null));
  }, []);

  // Saving and sending to a Telegram user are Gold features; viewing,
  // ticking and sharing the link work for everyone who has the link.
  const isGold = !!currentUser?.access.lists;
  const cheapestTotal = items
    .filter((i) => !i.checked && i.min_price !== null)
    .reduce((sum, i) => sum + (i.min_price as number), 0);

  const shareToTelegram = () => {
    const text = `${at(lang, 'shareMessage')}\n${telegramBotLink(`list_${data.id}`)}`;
    const url = `https://t.me/share/url?url=${encodeURIComponent(window.location.href)}&text=${encodeURIComponent(text)}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const sendToUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!recipient.trim()) return;
    setSendState('sending');
    try {
      await listsAPI.sendTelegram(data.id, recipient.trim(), lang);
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
      const response = await listsAPI.save(data.id, nameInput.trim(), lang);
      setSaved(true);
      setListName(response.data.name);
      setNamingOpen(false);
    } catch (err: any) {
      console.error('Failed to save list:', err);
      setSaveError(err?.response?.data?.detail || 'Failed to save list.');
    } finally {
      setSaving(false);
    }
  };

  const toggle = async (productId: string) => {
    // optimistic toggle - the backend persists the flip so anyone else
    // viewing the same shared link picks it up on their next fetch/reload
    setItems((prev) => prev.map((i) => (i.product_id === productId ? { ...i, checked: !i.checked } : i)));
    try {
      await listsAPI.toggleItem(data.id, productId, lang);
    } catch (err) {
      console.error('Failed to toggle item:', err);
      setItems((prev) => prev.map((i) => (i.product_id === productId ? { ...i, checked: !i.checked } : i)));
    }
  };

  const share = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy link:', err);
    }
  };

  return (
    <div className="w-full max-w-[42rem] mx-auto" style={{ fontFamily: 'inherit' }}>
      <div className="flex items-center justify-between mb-4 px-1 gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold" style={{ color: '#0f3d2e' }}>
            {listName || t.title}
          </h1>
          <p className="text-sm" style={{ color: '#7d9a8d' }}>
            {t.itemsCount(items.length)}
            {cheapestTotal > 0 && ` · ${at(lang, 'cheapestTotal')}: ${formatPrice(cheapestTotal, lang, data.country)}`}
          </p>
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
          {isGold && (saved ? (
            <span className="text-sm font-medium" style={{ color: '#05603a' }}>
              {t.saved}
            </span>
          ) : (
            <button
              onClick={() => setNamingOpen(true)}
              className="rounded-full text-sm font-semibold"
              style={{ padding: '8px 16px', backgroundColor: 'white', color: accent, border: `1px solid ${accent}`, cursor: 'pointer' }}
            >
              {t.save}
            </button>
          ))}
          <button
            onClick={share}
            className="rounded-full text-sm font-semibold"
            style={{
              padding: '8px 16px',
              backgroundColor: copied ? '#d8f3e3' : accent,
              color: copied ? '#05603a' : 'white',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            {copied ? t.copied : t.share}
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-4 px-1 flex-wrap">
        <button
          onClick={shareToTelegram}
          className="rounded-full text-sm font-semibold"
          style={{ padding: '8px 16px', backgroundColor: '#229ED9', color: 'white', border: 'none', cursor: 'pointer' }}
        >
          ✈️ {at(lang, 'shareTelegram')}
        </button>
        <a
          href={telegramBotLink(`list_${data.id}`)}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-full text-sm font-semibold"
          style={{ padding: '8px 16px', backgroundColor: 'white', color: '#229ED9', border: '1px solid #229ED9' }}
        >
          {at(lang, 'openInBot')}
        </a>
      </div>

      {isGold && (
        <form onSubmit={sendToUser} className="mb-4 px-1">
          <label className="block text-xs font-medium mb-1" style={{ color: '#52736a' }}>
            {at(lang, 'sendToUser')}
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
              className="flex-1 px-3 py-2 border rounded-lg text-sm"
              style={{ borderColor: '#d0d9d5' }}
            />
            <button
              type="submit"
              disabled={!recipient.trim() || sendState === 'sending'}
              className="px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap"
              style={{ backgroundColor: sendState === 'sent' ? '#d8f3e3' : '#229ED9', color: sendState === 'sent' ? '#05603a' : 'white', border: 'none', cursor: 'pointer' }}
            >
              {sendState === 'sent' ? at(lang, 'sent') : at(lang, 'send')}
            </button>
          </div>
          {sendState === 'notFound' && (
            <p className="text-xs mt-2" style={{ color: '#b45309' }}>
              {at(lang, 'userNotFound', { bot: TELEGRAM_BOT_USERNAME })}
            </p>
          )}
          {sendState === 'error' && <p className="text-xs mt-2 text-red-600">{at(lang, 'error')}</p>}
        </form>
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
              className="flex-1 px-3 py-2 border rounded-lg text-sm"
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
                    {formatPrice(item.min_price, lang, data.country)}
                  </div>
                  {item.cheapest_store && (
                    <div className="text-[10px]" style={{ color: '#a3b5ae' }}>
                      {t.cheapestAt} {item.cheapest_store}
                    </div>
                  )}
                </div>
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
                          {price === null ? '—' : formatPrice(price, lang, data.country)}
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
    </div>
  );
}
