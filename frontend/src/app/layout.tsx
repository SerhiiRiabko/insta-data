/**
 * Root Layout
 * Note: Since we use next-intl, the actual app layout is in [lang]/layout.tsx
 */

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Insta-Data - Порівняння цін',
  description: 'Порівнюйте ціни на харчові товари у Чорногорії',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}