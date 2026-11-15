'use client';

/**
 * Account: plan status, Telegram connection (link / unlink), email+password
 * for accounts that started in the bot, logout. Linking runs the same
 * "open the bot -> confirm -> poll" flow as Telegram login.
 */

import Link from 'next/link';
import { useRef, useState } from 'react';
import { authAPI, type CurrentUser } from '@/lib/api';
import { at, formatDate, planLabel } from '@/lib/accountText';
import type { Lang } from '@/lib/productMatrix';
import { openPendingTab, sendTabTo, useTelegramPoll } from '@/lib/telegramFlow';

interface AccountModalProps {
  isOpen: boolean;
  onClose: () => void;
  lang: Lang;
  user: CurrentUser;
  onUserChange: (user: CurrentUser) => void;
  onLogout: () => void;
  onOpenPlans: () => void;
}

export function AccountModal({ isOpen, onClose, lang, user, onUserChange, onLogout, onOpenPlans }: AccountModalProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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

  if (!isOpen) return null;

  const connectTelegram = async () => {
    setError(null);
    const tab = openPendingTab();
    try {
      const res = await authAPI.telegramLink();
      linkToken.current = res.data.token;
      setBotUrl(res.data.url);
      sendTabTo(tab, res.data.url);
      link.start();
    } catch {
      tab?.close();
      setError(at(lang, 'error'));
    }
  };

  const disconnectTelegram = async () => {
    setError(null);
    try {
      const res = await authAPI.telegramUnlink();
      onUserChange(res.data);
      link.reset();
    } catch {
      setError(at(lang, 'error'));
    }
  };

  const saveCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await authAPI.setCredentials(email, password);
      onUserChange(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail === 'email_taken_link_from_it' ? at(lang, 'emailTaken') : err?.response?.data?.detail || at(lang, 'error'));
    } finally {
      setBusy(false);
    }
  };

  const { access } = user;
  const telegramName = user.telegram ? (user.telegram.username ? `@${user.telegram.username}` : user.telegram.first_name || String(user.telegram.id)) : null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[10001] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-[26rem] w-full max-h-[90vh] overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold" style={{ color: '#0f3d2e' }}>
            {at(lang, 'account')}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl" aria-label="Close">
            ✕
          </button>
        </div>

        <p className="text-sm mb-4 break-all" style={{ color: '#33524a' }}>
          {user.email || telegramName}
        </p>

        <section className="rounded-xl p-4 mb-3" style={{ backgroundColor: '#f6faf8', border: '1px solid #e3eee8' }}>
          <div className="text-xs font-semibold uppercase mb-1" style={{ color: '#7d9a8d', letterSpacing: '0.05em' }}>
            {at(lang, 'plan')}
          </div>
          <div className="font-semibold mb-3" style={{ color: '#0f3d2e' }}>
            {planLabel(lang, access.plan)}
            {access.plan !== 'free' && (
              <span className="font-normal text-sm" style={{ color: '#52736a' }}>
                {' · '}
                {access.forever ? at(lang, 'forever') : access.expires_at ? at(lang, 'until', { date: formatDate(access.expires_at, lang) }) : ''}
              </span>
            )}
          </div>
          {access.plan !== 'gold' && (
            <button
              onClick={onOpenPlans}
              className="w-full py-2 rounded-lg font-semibold text-sm"
              style={{ backgroundColor: '#0b6e4f', color: 'white', border: 'none', cursor: 'pointer' }}
            >
              {at(lang, 'upgrade')}
            </button>
          )}
        </section>

        <section className="rounded-xl p-4 mb-3" style={{ border: '1px solid #e3eee8' }}>
          <div className="text-xs font-semibold uppercase mb-2" style={{ color: '#7d9a8d', letterSpacing: '0.05em' }}>
            {at(lang, 'telegram')}
          </div>
          {telegramName ? (
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm" style={{ color: '#0f1419' }}>
                {at(lang, 'connectedAs', { name: telegramName })}
              </span>
              {user.email && user.has_password && (
                <button
                  onClick={disconnectTelegram}
                  className="text-xs font-medium"
                  style={{ color: '#dc2626', background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  {at(lang, 'disconnect')}
                </button>
              )}
            </div>
          ) : (
            <>
              <button
                onClick={connectTelegram}
                disabled={link.state === 'waiting'}
                className="w-full py-2 rounded-lg font-semibold text-sm"
                style={{ backgroundColor: '#229ED9', color: 'white', border: 'none', cursor: link.state === 'waiting' ? 'default' : 'pointer' }}
              >
                ✈️ {at(lang, 'connectTelegram')}
              </button>
              {link.state === 'waiting' && (
                <p className="text-xs mt-2" style={{ color: '#33524a' }}>
                  {at(lang, 'confirmInTelegram')}{' '}
                  {botUrl && (
                    <a href={botUrl} target="_blank" rel="noopener noreferrer" style={{ color: '#229ED9' }}>
                      {at(lang, 'openBotAgain')}
                    </a>
                  )}
                </p>
              )}
              {link.state === 'failed' && <p className="text-xs mt-2 text-red-600">{at(lang, 'linkFailed')}</p>}
              {link.state === 'expired' && <p className="text-xs mt-2 text-red-600">{at(lang, 'expired')}</p>}
            </>
          )}
        </section>

        {!user.email && (
          <section className="rounded-xl p-4 mb-3" style={{ border: '1px solid #e3eee8' }}>
            <div className="text-sm font-semibold mb-1" style={{ color: '#0f3d2e' }}>
              {at(lang, 'addCredentials')}
            </div>
            <p className="text-xs mb-3" style={{ color: '#7d9a8d' }}>
              {at(lang, 'credentialsHint')}
            </p>
            <form onSubmit={saveCredentials} className="flex flex-col gap-2">
              <input
                type="email"
                required
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm"
                style={{ borderColor: '#d0d9d5' }}
              />
              <input
                type="password"
                required
                minLength={8}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm"
                style={{ borderColor: '#d0d9d5' }}
              />
              <button
                type="submit"
                disabled={busy}
                className="w-full py-2 rounded-lg font-semibold text-sm"
                style={{ backgroundColor: '#0b6e4f', color: 'white', border: 'none', cursor: busy ? 'default' : 'pointer' }}
              >
                {at(lang, 'save')}
              </button>
            </form>
          </section>
        )}

        {error && <p className="text-sm mb-3 text-red-600">{error}</p>}

        <div className="flex items-center justify-between mt-2">
          {user.is_admin ? (
            <Link href={`/${lang}/admin`} className="text-sm font-medium" style={{ color: '#0b6e4f' }}>
              {at(lang, 'admin')}
            </Link>
          ) : (
            <span />
          )}
          <button
            onClick={onLogout}
            className="text-sm font-medium"
            style={{ color: '#52736a', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            {at(lang, 'logout')}
          </button>
        </div>
      </div>
    </div>
  );
}
