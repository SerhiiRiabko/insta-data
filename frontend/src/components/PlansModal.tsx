'use client';

/**
 * Plans: Compare (all stores side by side) and Gold (compare + shopping
 * lists and sharing). Pay with Telegram Stars - needs a linked Telegram, so
 * an unlinked user first goes through the link flow, after which the bot
 * offers the invoice itself - or by card transfer, which an admin confirms.
 */

import { useEffect, useRef, useState } from 'react';
import { authAPI, subscriptionsAPI, type CurrentUser, type Plan } from '@/lib/api';
import { at, formatDate, planLabel } from '@/lib/accountText';
import type { Lang } from '@/lib/productMatrix';
import { openPendingTab, sendTabTo, useTelegramPoll } from '@/lib/telegramFlow';

interface PlanInfo {
  id: Plan;
  stars: number;
  eur: number;
}

interface PlansData {
  plans: PlanInfo[];
  card_available: boolean;
  card_details: string;
  bot_username: string;
}

interface PlansModalProps {
  isOpen: boolean;
  onClose: () => void;
  lang: Lang;
  currentUser: CurrentUser | null;
  onNeedLogin: () => void;
  onUserChange: (user: CurrentUser) => void;
  highlight?: Plan;
}

type View = { kind: 'plans' } | { kind: 'card'; plan: PlanInfo } | { kind: 'message'; text: string };

export function PlansModal({ isOpen, onClose, lang, currentUser, onNeedLogin, onUserChange, highlight }: PlansModalProps) {
  const [data, setData] = useState<PlansData | null>(null);
  const [pending, setPending] = useState<Plan[]>([]);
  const [view, setView] = useState<View>({ kind: 'plans' });
  const [comment, setComment] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const linkToken = useRef<string | null>(null);
  const [botUrl, setBotUrl] = useState<string | null>(null);

  const link = useTelegramPoll(async () => {
    if (!linkToken.current) return 'failed';
    const res = await authAPI.telegramLinkStatus(linkToken.current);
    if (res.data.status === 'linked') {
      onUserChange(res.data.user);
      return 'done';
    }
    return res.data.status === 'failed' ? 'failed' : 'pending';
  });

  useEffect(() => {
    if (!isOpen) return;
    setView({ kind: 'plans' });
    setError(null);
    link.reset();
    subscriptionsAPI.plans().then((res) => setData(res.data)).catch(() => setData(null));
    if (currentUser) {
      subscriptionsAPI
        .me()
        .then((res) => setPending(res.data.pending_requests.map((r: { plan: Plan }) => r.plan)))
        .catch(() => setPending([]));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, currentUser?.id]);

  if (!isOpen) return null;

  const payStars = async (plan: PlanInfo) => {
    if (!currentUser) return onNeedLogin();
    setError(null);
    const tab = openPendingTab();
    try {
      if (!currentUser.telegram) {
        const res = await authAPI.telegramLink(plan.id);
        linkToken.current = res.data.token;
        setBotUrl(res.data.url);
        sendTabTo(tab, res.data.url);
        link.start();
        return;
      }
      const res = await subscriptionsAPI.starsInvoice(plan.id, lang);
      sendTabTo(tab, res.data.url);
      setView({ kind: 'message', text: at(lang, 'invoiceOpened') });
    } catch {
      tab?.close();
      setError(at(lang, 'error'));
    }
  };

  const openCard = (plan: PlanInfo) => {
    if (!currentUser) return onNeedLogin();
    setComment('');
    setError(null);
    setView({ kind: 'card', plan });
  };

  const submitCard = async (plan: PlanInfo) => {
    setBusy(true);
    setError(null);
    try {
      await subscriptionsAPI.cardRequest(plan.id, comment);
      setPending((p) => [...p, plan.id]);
      setView({ kind: 'message', text: at(lang, 'requestSent') });
    } catch {
      setError(at(lang, 'error'));
    } finally {
      setBusy(false);
    }
  };

  const access = currentUser?.access;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[10001] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-[40rem] w-full max-h-[90vh] overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold" style={{ color: '#0f3d2e' }}>
            {at(lang, 'plansTitle')}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl" aria-label="Close">
            ✕
          </button>
        </div>
        <p className="text-sm mb-4" style={{ color: '#52736a' }}>
          {at(lang, 'bothPlaces')}
        </p>

        {access && (
          <p className="text-sm mb-4 font-medium" style={{ color: '#0f3d2e' }}>
            {at(lang, 'currentPlan')}: {planLabel(lang, access.plan)}
            {access.plan !== 'free' && (access.forever ? ` · ${at(lang, 'forever')}` : access.expires_at ? ` · ${at(lang, 'until', { date: formatDate(access.expires_at, lang) })}` : '')}
          </p>
        )}

        {link.state === 'waiting' && (
          <div className="rounded-lg p-3 mb-4 text-sm" style={{ backgroundColor: '#eaf6fd', color: '#14527a' }}>
            <p className="mb-1">{at(lang, 'starsNeedTelegram')}</p>
            <p>
              {at(lang, 'confirmInTelegram')}{' '}
              {botUrl && (
                <a href={botUrl} target="_blank" rel="noopener noreferrer" style={{ color: '#229ED9' }}>
                  {at(lang, 'openBotAgain')}
                </a>
              )}
            </p>
          </div>
        )}
        {link.state === 'done' && (
          <div className="rounded-lg p-3 mb-4 text-sm" style={{ backgroundColor: '#d8f3e3', color: '#05603a' }}>
            {at(lang, 'invoiceOpened')}
          </div>
        )}
        {link.state === 'failed' && <p className="text-sm mb-4 text-red-600">{at(lang, 'linkFailed')}</p>}
        {link.state === 'expired' && <p className="text-sm mb-4 text-red-600">{at(lang, 'expired')}</p>}
        {error && <p className="text-sm mb-4 text-red-600">{error}</p>}

        {view.kind === 'message' && (
          <div className="rounded-lg p-4 text-sm" style={{ backgroundColor: '#d8f3e3', color: '#05603a' }}>
            {view.text}
          </div>
        )}

        {view.kind === 'card' && data && (
          <div>
            <button
              onClick={() => setView({ kind: 'plans' })}
              className="text-xs font-medium mb-3"
              style={{ color: '#52736a', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              {at(lang, 'back')}
            </button>
            <h3 className="font-semibold mb-2" style={{ color: '#0f3d2e' }}>
              {at(lang, 'cardTitle')} · {planLabel(lang, view.plan.id)}
            </h3>
            <p className="text-sm mb-3" style={{ color: '#33524a' }}>
              {at(lang, 'cardSteps', { eur: view.plan.eur })}
            </p>
            <pre
              className="text-sm rounded-lg p-3 mb-3 whitespace-pre-wrap break-words"
              style={{ backgroundColor: '#f6faf8', border: '1px solid #e3eee8', color: '#0f1419', fontFamily: 'Space Grotesk, monospace' }}
            >
              {data.card_details}
            </pre>
            <input
              type="text"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={at(lang, 'commentPlaceholder')}
              maxLength={200}
              className="w-full px-3 py-2.5 border rounded-lg text-sm mb-3"
              style={{ borderColor: '#d0d9d5' }}
            />
            <button
              onClick={() => submitCard(view.plan)}
              disabled={busy}
              className="w-full py-2.5 rounded-lg font-semibold text-sm"
              style={{ backgroundColor: '#0b6e4f', color: 'white', border: 'none', cursor: busy ? 'default' : 'pointer' }}
            >
              {at(lang, 'iPaid')}
            </button>
          </div>
        )}

        {view.kind === 'plans' && data && (
          <div className="grid gap-3 sm:grid-cols-2">
            {data.plans.map((plan) => {
              const active = access?.plan === plan.id || (plan.id === 'compare' && access?.plan === 'gold');
              const isHighlighted = highlight === plan.id;
              return (
                <div
                  key={plan.id}
                  className="rounded-xl p-4 flex flex-col"
                  style={{
                    border: `2px solid ${isHighlighted ? '#0b6e4f' : '#e3eee8'}`,
                    backgroundColor: plan.id === 'gold' ? '#fffaf0' : 'white',
                  }}
                >
                  <div className="flex items-baseline justify-between mb-1">
                    <span className="font-bold text-lg" style={{ color: '#0f3d2e' }}>
                      {plan.id === 'gold' ? '⭐ ' : ''}
                      {planLabel(lang, plan.id)}
                    </span>
                    {active && (
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full" style={{ backgroundColor: '#d8f3e3', color: '#05603a' }}>
                        ✓
                      </span>
                    )}
                  </div>
                  <p className="text-sm mb-3 flex-1" style={{ color: '#52736a' }}>
                    {at(lang, plan.id === 'gold' ? 'goldDesc' : 'compareDesc')}
                  </p>
                  <p className="text-sm font-semibold mb-3" style={{ color: '#0f3d2e', fontFamily: 'Space Grotesk, monospace' }}>
                    {plan.eur} € · {plan.stars} ⭐ <span style={{ fontWeight: 400, color: '#7d9a8d' }}>{at(lang, 'perMonth')}</span>
                  </p>
                  <button
                    onClick={() => payStars(plan)}
                    className="w-full py-2 rounded-lg font-semibold text-sm mb-2"
                    style={{ backgroundColor: '#229ED9', color: 'white', border: 'none', cursor: 'pointer' }}
                  >
                    {at(lang, 'payStars', { stars: plan.stars })}
                  </button>
                  {data.card_available && (
                    <button
                      onClick={() => openCard(plan)}
                      disabled={pending.includes(plan.id)}
                      className="w-full py-2 rounded-lg font-semibold text-sm"
                      style={{
                        backgroundColor: 'white',
                        color: pending.includes(plan.id) ? '#a3b5ae' : '#0b6e4f',
                        border: '1px solid #0b6e4f',
                        cursor: pending.includes(plan.id) ? 'default' : 'pointer',
                      }}
                    >
                      {pending.includes(plan.id) ? at(lang, 'pendingReview') : at(lang, 'payCard', { eur: plan.eur })}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {!currentUser && view.kind === 'plans' && (
          <button
            onClick={onNeedLogin}
            className="w-full mt-4 py-2.5 rounded-lg font-semibold text-sm"
            style={{ backgroundColor: '#0b6e4f', color: 'white', border: 'none', cursor: 'pointer' }}
          >
            {at(lang, 'loginToBuy')}
          </button>
        )}
      </div>
    </div>
  );
}
