import { AdminPageClient } from './AdminPageClient';

export default async function AdminPage({
  params,
}: {
  params: Promise<{ lang: string }>;
}) {
  await params;
  return <AdminPageClient />;
}