import { ListPageClient } from './ListPageClient';

export default async function ListPage({
  params,
}: {
  params: Promise<{ lang: string; id: string }>;
}) {
  const { lang, id } = await params;
  return <ListPageClient urlLang={lang} listId={id} />;
}
