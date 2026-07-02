/**
 * Header Component
 * Navigation + Language Selector
 */

'use client';

import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { locales } from '@/i18n';

interface HeaderProps {
  lang: string;
}

export function Header({ lang }: HeaderProps) {
  const t = useTranslations();
  const router = useRouter();
  const [isLanguageOpen, setIsLanguageOpen] = useState(false);

  const handleLanguageChange = (newLang: string) => {
    router.push(`/${newLang}`);
    setIsLanguageOpen(false);
  };

  return (
    <header className="bg-neutral-800 border-b border-neutral-700 sticky top-0 z-50">
      <div className="container-max flex justify-between items-center py-4">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary-700 flex items-center justify-center">
            <span className="text-accent-500 font-bold">📊</span>
          </div>
          <h1 className="text-lg font-bold text-neutral-50">{t('app.name')}</h1>
        </div>

        {/* Navigation */}
        <nav className="hidden md:flex gap-6 items-center">
          <a href="#search" className="text-neutral-300 hover:text-primary-400 transition-colors">
            {t('header.search')}
          </a>
        </nav>

        {/* Language Selector */}
        <div className="relative">
          <button
            onClick={() => setIsLanguageOpen(!isLanguageOpen)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-neutral-700 hover:bg-neutral-600 transition-colors text-neutral-50 text-sm font-medium"
          >
            <span>🌍</span>
            <span className="uppercase">{lang}</span>
          </button>

          {isLanguageOpen && (
            <div className="absolute right-0 mt-2 bg-neutral-700 rounded-lg shadow-lg overflow-hidden z-50">
              {locales.map((locale) => (
                <button
                  key={locale}
                  onClick={() => handleLanguageChange(locale)}
                  className={`w-full px-4 py-2 text-left text-sm transition-colors ${
                    lang === locale
                      ? 'bg-primary-600 text-white'
                      : 'text-neutral-300 hover:bg-neutral-600'
                  }`}
                >
                  {locale === 'ukr' && '🇺🇦 Українська'}
                  {locale === 'rus' && '🇷🇺 Русский'}
                  {locale === 'mne' && '🇲🇪 Crnogorski'}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}