'use client';

import { useState } from 'react';
import { authAPI } from '@/lib/api';
import { ALL_LANGS, type Lang } from '@/lib/productMatrix';

type Method = 'magic' | 'password';
type PasswordMode = 'login' | 'register';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthenticated: (user: { id: string; email: string; tier: string }) => void;
  lang: Lang;
}

type AuthText = {
  title: string; magicTab: string; passwordTab: string; email: string; password: string;
  sendLink: string; sending: string; linkSent: string; login: string; register: string;
  switchToRegister: string; switchToLogin: string; submitting: string; passwordHint: string;
};

const translations: Record<Lang, AuthText> = {
  rus: {
    title: 'Вход',
    magicTab: 'Волшебная ссылка',
    passwordTab: 'Пароль',
    email: 'Email',
    password: 'Пароль',
    sendLink: 'Отправить ссылку',
    sending: 'Отправляем…',
    linkSent: 'Проверьте почту — мы отправили ссылку для входа. Действительна 15 минут.',
    login: 'Войти',
    register: 'Зарегистрироваться',
    switchToRegister: 'Нет аккаунта? Зарегистрироваться',
    switchToLogin: 'Уже есть аккаунт? Войти',
    submitting: 'Подождите…',
    passwordHint: 'Минимум 8 символов',
  },
  ukr: {
    title: 'Вхід',
    magicTab: 'Магічне посилання',
    passwordTab: 'Пароль',
    email: 'Email',
    password: 'Пароль',
    sendLink: 'Надіслати посилання',
    sending: 'Надсилаємо…',
    linkSent: 'Перевірте пошту — ми надіслали посилання для входу. Дійсне 15 хвилин.',
    login: 'Увійти',
    register: 'Зареєструватися',
    switchToRegister: 'Немає акаунта? Зареєструватися',
    switchToLogin: 'Вже є акаунт? Увійти',
    submitting: 'Зачекайте…',
    passwordHint: 'Мінімум 8 символів',
  },
  eng: {
    title: 'Sign in',
    magicTab: 'Magic link',
    passwordTab: 'Password',
    email: 'Email',
    password: 'Password',
    sendLink: 'Send link',
    sending: 'Sending…',
    linkSent: 'Check your inbox — we sent a login link. Valid for 15 minutes.',
    login: 'Log in',
    register: 'Sign up',
    switchToRegister: "Don't have an account? Sign up",
    switchToLogin: 'Already have an account? Log in',
    submitting: 'Please wait…',
    passwordHint: 'Minimum 8 characters',
  },
  mne: {
    title: 'Prijava',
    magicTab: 'Magični link',
    passwordTab: 'Lozinka',
    email: 'Email',
    password: 'Lozinka',
    sendLink: 'Pošalji link',
    sending: 'Šaljemo…',
    linkSent: 'Provjerite e-poštu — poslali smo link za prijavu. Važi 15 minuta.',
    login: 'Prijavi se',
    register: 'Registruj se',
    switchToRegister: 'Nemate nalog? Registrujte se',
    switchToLogin: 'Već imate nalog? Prijavite se',
    submitting: 'Sačekajte…',
    passwordHint: 'Minimum 8 karaktera',
  },
  srb: {
    title: 'Prijava',
    magicTab: 'Magični link',
    passwordTab: 'Lozinka',
    email: 'Email',
    password: 'Lozinka',
    sendLink: 'Pošalji link',
    sending: 'Šaljemo…',
    linkSent: 'Proverite e-poštu — poslali smo link za prijavu. Važi 15 minuta.',
    login: 'Prijavi se',
    register: 'Registruj se',
    switchToRegister: 'Nemate nalog? Registrujte se',
    switchToLogin: 'Već imate nalog? Prijavite se',
    submitting: 'Sačekajte…',
    passwordHint: 'Minimum 8 karaktera',
  },
  bos: {
    title: 'Prijava',
    magicTab: 'Magični link',
    passwordTab: 'Lozinka',
    email: 'Email',
    password: 'Lozinka',
    sendLink: 'Pošalji link',
    sending: 'Šaljemo…',
    linkSent: 'Provjerite e-poštu — poslali smo link za prijavu. Važi 15 minuta.',
    login: 'Prijavi se',
    register: 'Registruj se',
    switchToRegister: 'Nemate nalog? Registrujte se',
    switchToLogin: 'Već imate nalog? Prijavite se',
    submitting: 'Sačekajte…',
    passwordHint: 'Minimum 8 karaktera',
  },
};

function urlLocale(): string {
  if (typeof window === 'undefined') return 'ukr';
  const seg = window.location.pathname.split('/')[1];
  return (ALL_LANGS as string[]).includes(seg) ? seg : 'ukr';
}

export function AuthModal({ isOpen, onClose, onAuthenticated, lang }: AuthModalProps) {
  const t = translations[lang];
  const [method, setMethod] = useState<Method>('magic');
  const [mode, setMode] = useState<PasswordMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [linkSent, setLinkSent] = useState(false);

  if (!isOpen) return null;

  const sendMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await authAPI.magicLinkRequest(email, urlLocale());
      setLinkSent(true);
    } catch {
      setError('Failed to send link. Try again.');
    } finally {
      setBusy(false);
    }
  };

  const submitPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const response = mode === 'login' ? await authAPI.login(email, password) : await authAPI.register(email, password);
      onAuthenticated(response.data);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Something went wrong.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[10001] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-[24rem] w-full p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-bold" style={{ color: '#0f3d2e' }}>
            {t.title}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl" aria-label="Close">
            ✕
          </button>
        </div>

        <div className="flex mb-5 rounded-lg overflow-hidden border" style={{ borderColor: '#e3eee8' }}>
          {(['magic', 'password'] as Method[]).map((m) => (
            <button
              key={m}
              onClick={() => {
                setMethod(m);
                setError(null);
                setLinkSent(false);
              }}
              className="flex-1 text-sm font-semibold"
              style={{
                padding: '10px 8px',
                backgroundColor: method === m ? '#0b6e4f' : 'white',
                color: method === m ? 'white' : '#52736a',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              {m === 'magic' ? t.magicTab : t.passwordTab}
            </button>
          ))}
        </div>

        {method === 'magic' ? (
          linkSent ? (
            <p className="text-sm text-center py-4" style={{ color: '#33524a' }}>
              {t.linkSent}
            </p>
          ) : (
            <form onSubmit={sendMagicLink} className="flex flex-col gap-3">
              <input
                type="email"
                required
                placeholder={t.email}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2.5 border rounded-lg text-sm"
                style={{ borderColor: '#d0d9d5' }}
              />
              {error && <p className="text-xs text-red-600">{error}</p>}
              <button
                type="submit"
                disabled={busy}
                className="w-full py-2.5 rounded-lg font-semibold text-sm"
                style={{ backgroundColor: '#0b6e4f', color: 'white', border: 'none', cursor: busy ? 'default' : 'pointer' }}
              >
                {busy ? t.sending : t.sendLink}
              </button>
            </form>
          )
        ) : (
          <form onSubmit={submitPassword} className="flex flex-col gap-3">
            <input
              type="email"
              required
              placeholder={t.email}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 border rounded-lg text-sm"
              style={{ borderColor: '#d0d9d5' }}
            />
            <input
              type="password"
              required
              minLength={mode === 'register' ? 8 : undefined}
              placeholder={t.password}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 border rounded-lg text-sm"
              style={{ borderColor: '#d0d9d5' }}
            />
            {mode === 'register' && (
              <p className="text-xs" style={{ color: '#a3b5ae' }}>
                {t.passwordHint}
              </p>
            )}
            {error && <p className="text-xs text-red-600">{error}</p>}
            <button
              type="submit"
              disabled={busy}
              className="w-full py-2.5 rounded-lg font-semibold text-sm"
              style={{ backgroundColor: '#0b6e4f', color: 'white', border: 'none', cursor: busy ? 'default' : 'pointer' }}
            >
              {busy ? t.submitting : mode === 'login' ? t.login : t.register}
            </button>
            <button
              type="button"
              onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
              className="text-xs text-center"
              style={{ color: '#52736a', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              {mode === 'login' ? t.switchToRegister : t.switchToLogin}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}