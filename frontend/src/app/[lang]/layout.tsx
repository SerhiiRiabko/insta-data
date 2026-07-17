/**
 * Localized Layout with i18n
 * Routes: /ukr, /rus, /mne
 */

import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { locales } from '@/i18n';
import { BCP47_TAG } from '@/lib/productMatrix';
import '@/app/globals.css';

export const metadata: Metadata = {
  title: 'Monte-Shop-Price - Real-time Price Comparison',
  description: 'Find the best prices for grocery products in Montenegro',
};

export function generateStaticParams() {
  return locales.map((locale) => ({ lang: locale }));
}

export default async function RootLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;
  if (!locales.includes(lang as any)) {
    notFound();
  }

  return (
    <html lang={BCP47_TAG[lang as keyof typeof BCP47_TAG] ?? lang}>
      <body>{children}</body>
    </html>
  );
}