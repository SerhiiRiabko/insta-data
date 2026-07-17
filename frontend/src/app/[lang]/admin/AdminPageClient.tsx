'use client';

import { useEffect, useState } from 'react';
import { adminAPI, authAPI, storesAPI, scraperAgentsAPI, type StoreInput, type ScraperAgentInput } from '@/lib/api';
import { AuthModal } from '@/components/AuthModal';

type CurrentUser = { id: string; email: string; tier: string; is_admin: boolean };

interface StoreRow {
  id: string;
  name: string;
  initial: string;
  color: string;
  url: string;
  active: boolean;
}

interface UserRow {
  id: string;
  email: string;
  tier: string;
  is_admin: boolean;
  created_at: string;
}

interface ScraperAgentRow {
  id: string;
  name: string;
  strategy: 'cijene' | 'instagram' | 'custom';
  store_ids: string[];
  url: string | null;
  active: boolean;
  runnable: boolean;
  last_run_at: string | null;
  last_run_status: string;
  last_run_products_found: number | null;
  last_run_error: string | null;
}

const EMPTY_STORE: StoreInput = { name: '', initial: '', color: '#0b6e4f', url: '', active: true };
const EMPTY_AGENT: ScraperAgentInput = { name: '', strategy: 'custom', store_ids: [], url: '', active: true };

export function AdminPageClient() {
  const [currentUser, setCurrentUser] = useState<CurrentUser | null | 'loading'>('loading');
  const [tab, setTab] = useState<'stores' | 'scrapers' | 'tiers' | 'users'>('stores');

  useEffect(() => {
    authAPI
      .me()
      .then((res) => setCurrentUser(res.data))
      .catch(() => setCurrentUser(null));
  }, []);

  if (currentUser === 'loading') {
    return <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#f5f3f0' }} />;
  }

  if (!currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#f5f3f0' }}>
        <AuthModal
          isOpen={true}
          onClose={() => {}}
          onAuthenticated={(user) => setCurrentUser(user as CurrentUser)}
          lang="ukr"
        />
      </div>
    );
  }

  if (!currentUser.is_admin) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#f5f3f0' }}>
        <p style={{ color: '#7d9a8d' }}>Доступ заборонено — цей акаунт не є адміністратором.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#f5f3f0' }}>
      <div className="max-w-4xl mx-auto py-10 px-4">
        <h1 className="text-2xl font-bold mb-1" style={{ color: '#0f3d2e' }}>
          Адмінка
        </h1>
        <p className="text-sm mb-6" style={{ color: '#7d9a8d' }}>
          {currentUser.email}
        </p>

        <div className="flex gap-1 mb-6 rounded-lg overflow-hidden border w-fit" style={{ borderColor: '#e3eee8' }}>
          {(['stores', 'scrapers', 'tiers', 'users'] as const).map((tb) => (
            <button
              key={tb}
              onClick={() => setTab(tb)}
              className="text-sm font-semibold"
              style={{
                padding: '10px 20px',
                backgroundColor: tab === tb ? '#0b6e4f' : 'white',
                color: tab === tb ? 'white' : '#52736a',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              {tb === 'stores' ? 'Магазини' : tb === 'scrapers' ? 'Скрейпери' : tb === 'tiers' ? 'Тарифи' : 'Юзери'}
            </button>
          ))}
        </div>

        {tab === 'stores' && <StoresTab />}
        {tab === 'scrapers' && <ScrapersTab />}
        {tab === 'tiers' && <TiersTab />}
        {tab === 'users' && <UsersTab />}
      </div>
    </div>
  );
}

function StoresTab() {
  const [stores, setStores] = useState<StoreRow[]>([]);
  const [editing, setEditing] = useState<StoreRow | null>(null);
  const [form, setForm] = useState<StoreInput>(EMPTY_STORE);
  const [creating, setCreating] = useState(false);

  const load = () => storesAPI.list(true).then((res) => setStores(res.data.stores));

  useEffect(() => {
    load();
  }, []);

  const startEdit = (s: StoreRow) => {
    setEditing(s);
    setForm({ name: s.name, initial: s.initial, color: s.color, url: s.url, active: s.active });
  };

  const startCreate = () => {
    setEditing(null);
    setCreating(true);
    setForm(EMPTY_STORE);
  };

  const save = async () => {
    if (editing) {
      await storesAPI.update(editing.id, form);
    } else {
      await storesAPI.create(form);
    }
    setEditing(null);
    setCreating(false);
    load();
  };

  const deactivate = async (id: string) => {
    await storesAPI.deactivate(id);
    load();
  };

  return (
    <div className="bg-white rounded-2xl border" style={{ borderColor: '#e3eee8' }}>
      <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: '#f0f0f0' }}>
        <h2 className="font-semibold" style={{ color: '#0f3d2e' }}>
          Магазини
        </h2>
        <button
          onClick={startCreate}
          className="text-sm font-semibold rounded-lg"
          style={{ padding: '8px 14px', backgroundColor: '#0b6e4f', color: 'white', border: 'none', cursor: 'pointer' }}
        >
          + Додати сайт
        </button>
      </div>

      <div className="divide-y" style={{ borderColor: '#f0f0f0' }}>
        {stores.map((s) => (
          <div key={s.id} className="flex items-center gap-3 px-4 py-3">
            <span className="w-6 h-6 rounded flex-shrink-0" style={{ backgroundColor: s.color }} />
            <span className="font-medium flex-1" style={{ color: s.active ? '#0f1419' : '#a3b5ae' }}>
              {s.name} {!s.active && '(вимкнено)'}
            </span>
            <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-xs truncate" style={{ maxWidth: '240px', color: '#52736a' }}>
              {s.url}
            </a>
            <button onClick={() => startEdit(s)} className="text-xs font-medium" style={{ color: '#0b6e4f', background: 'none', border: 'none', cursor: 'pointer' }}>
              Редагувати
            </button>
            {s.active && (
              <button onClick={() => deactivate(s.id)} className="text-xs font-medium" style={{ color: '#dc2626', background: 'none', border: 'none', cursor: 'pointer' }}>
                Вимкнути
              </button>
            )}
          </div>
        ))}
      </div>

      {(editing || creating) && (
        <div className="p-4 border-t space-y-2" style={{ borderColor: '#f0f0f0' }}>
          <div className="grid grid-cols-2 gap-2">
            <input placeholder="Назва" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" style={{ borderColor: '#d0d9d5' }} />
            <input placeholder="Ініціал (1 літера)" value={form.initial} maxLength={2} onChange={(e) => setForm({ ...form, initial: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" style={{ borderColor: '#d0d9d5' }} />
            <input type="color" value={form.color} onChange={(e) => setForm({ ...form, color: e.target.value })} className="h-10 border rounded-lg" style={{ borderColor: '#d0d9d5' }} />
            <input placeholder="URL сайту" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" style={{ borderColor: '#d0d9d5' }} />
          </div>
          <div className="flex gap-2">
            <button onClick={save} className="text-sm font-semibold rounded-lg" style={{ padding: '8px 16px', backgroundColor: '#0b6e4f', color: 'white', border: 'none', cursor: 'pointer' }}>
              Зберегти
            </button>
            <button
              onClick={() => {
                setEditing(null);
                setCreating(false);
              }}
              className="text-sm"
              style={{ padding: '8px 16px', color: '#52736a', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              Скасувати
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

const STRATEGY_LABEL: Record<ScraperAgentInput['strategy'], string> = {
  cijene: 'Cijene.me (готовий парсер)',
  instagram: 'Instagram (мок)',
  custom: 'Кастомний сайт (потребує ручного парсера)',
};

const STATUS_LABEL: Record<string, string> = {
  never: 'Ще не запускався',
  success: '✓ Успішно',
  partial: '⚠ Частково',
  failed: '✗ Помилка',
  not_implemented: '⏳ Не реалізовано',
};

function ScrapersTab() {
  const [agents, setAgents] = useState<ScraperAgentRow[]>([]);
  const [stores, setStores] = useState<StoreRow[]>([]);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<ScraperAgentInput>(EMPTY_AGENT);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  const load = () => {
    scraperAgentsAPI.list().then((res) => setAgents(res.data.agents));
    storesAPI.list(true).then((res) => setStores(res.data.stores));
  };

  useEffect(() => {
    load();
  }, []);

  const storeName = (id: string) => stores.find((s) => s.id === id)?.name || id;

  const toggleStore = (id: string) => {
    setForm((f) => ({
      ...f,
      store_ids: f.store_ids.includes(id) ? f.store_ids.filter((x) => x !== id) : [...f.store_ids, id],
    }));
  };

  const save = async () => {
    await scraperAgentsAPI.create(form);
    setCreating(false);
    setForm(EMPTY_AGENT);
    load();
  };

  const deactivate = async (id: string) => {
    await scraperAgentsAPI.deactivate(id);
    load();
  };

  const run = async (id: string) => {
    setRunningId(id);
    setRunError(null);
    try {
      await scraperAgentsAPI.run(id);
    } catch (err: any) {
      setRunError(err?.response?.data?.detail || 'Не вдалося запустити.');
    } finally {
      setRunningId(null);
      load();
    }
  };

  return (
    <div className="bg-white rounded-2xl border" style={{ borderColor: '#e3eee8' }}>
      <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: '#f0f0f0' }}>
        <h2 className="font-semibold" style={{ color: '#0f3d2e' }}>
          Скрейпери
        </h2>
        <button
          onClick={() => {
            setCreating(true);
            setForm(EMPTY_AGENT);
          }}
          className="text-sm font-semibold rounded-lg"
          style={{ padding: '8px 14px', backgroundColor: '#0b6e4f', color: 'white', border: 'none', cursor: 'pointer' }}
        >
          + Додати сайт
        </button>
      </div>

      {runError && <p className="text-sm text-red-600 px-4 pt-3">{runError}</p>}

      <div className="divide-y" style={{ borderColor: '#f0f0f0' }}>
        {agents.map((a) => (
          <div key={a.id} className="flex items-center gap-3 px-4 py-3 flex-wrap">
            <span className="font-medium" style={{ color: a.active ? '#0f1419' : '#a3b5ae', minWidth: '160px' }}>
              {a.name} {!a.active && '(вимкнено)'}
            </span>
            <span className="text-xs" style={{ color: '#52736a' }}>
              {STRATEGY_LABEL[a.strategy]}
            </span>
            <span className="text-xs" style={{ color: '#52736a' }}>
              {a.store_ids.map(storeName).join(', ') || '—'}
            </span>
            <span className="text-xs flex-1" style={{ color: '#7d9a8d' }}>
              {STATUS_LABEL[a.last_run_status] || a.last_run_status}
              {a.last_run_products_found !== null && ` · ${a.last_run_products_found} товарів`}
              {a.last_run_at && ` · ${new Date(a.last_run_at).toLocaleString('uk-UA')}`}
              {a.last_run_error && a.last_run_status !== 'not_implemented' && (
                <span style={{ color: '#dc2626' }}> · {a.last_run_error}</span>
              )}
            </span>
            <button
              onClick={() => run(a.id)}
              disabled={!a.runnable || runningId === a.id}
              title={!a.runnable ? 'Потребує ручного парсера — див. документацію' : undefined}
              className="text-xs font-medium"
              style={{
                color: a.runnable ? '#0b6e4f' : '#a3b5ae',
                background: 'none',
                border: 'none',
                cursor: a.runnable ? 'pointer' : 'default',
              }}
            >
              {runningId === a.id ? 'Запускаємо…' : 'Запустити зараз'}
            </button>
            {a.active && (
              <button onClick={() => deactivate(a.id)} className="text-xs font-medium" style={{ color: '#dc2626', background: 'none', border: 'none', cursor: 'pointer' }}>
                Вимкнути
              </button>
            )}
          </div>
        ))}
      </div>

      {creating && (
        <div className="p-4 border-t space-y-2" style={{ borderColor: '#f0f0f0' }}>
          <div className="grid grid-cols-2 gap-2">
            <input
              placeholder="Назва"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="px-3 py-2 border rounded-lg text-sm"
              style={{ borderColor: '#d0d9d5' }}
            />
            <select
              value={form.strategy}
              onChange={(e) => setForm({ ...form, strategy: e.target.value as ScraperAgentInput['strategy'] })}
              className="px-3 py-2 border rounded-lg text-sm"
              style={{ borderColor: '#d0d9d5' }}
            >
              {(['custom', 'cijene', 'instagram'] as const).map((s) => (
                <option key={s} value={s}>
                  {STRATEGY_LABEL[s]}
                </option>
              ))}
            </select>
            <input
              placeholder="URL сайту"
              value={form.url || ''}
              onChange={(e) => setForm({ ...form, url: e.target.value })}
              className="px-3 py-2 border rounded-lg text-sm col-span-2"
              style={{ borderColor: '#d0d9d5' }}
            />
          </div>
          <div className="flex flex-wrap gap-3 text-sm" style={{ color: '#33524a' }}>
            {stores.map((s) => (
              <label key={s.id} className="flex items-center gap-1.5">
                <input type="checkbox" checked={form.store_ids.includes(s.id)} onChange={() => toggleStore(s.id)} />
                {s.name}
              </label>
            ))}
          </div>
          {form.strategy === 'custom' && (
            <p className="text-xs" style={{ color: '#a3b5ae' }}>
              Кастомний сайт зберігається як конфіг, але не запускається автоматично — для нового формату сайту
              потрібен окремий парсер, написаний вручну.
            </p>
          )}
          <div className="flex gap-2">
            <button
              onClick={save}
              disabled={!form.name}
              className="text-sm font-semibold rounded-lg"
              style={{ padding: '8px 16px', backgroundColor: '#0b6e4f', color: 'white', border: 'none', cursor: 'pointer' }}
            >
              Зберегти
            </button>
            <button
              onClick={() => setCreating(false)}
              className="text-sm"
              style={{ padding: '8px 16px', color: '#52736a', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              Скасувати
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function TiersTab() {
  const [limits, setLimits] = useState<{ free: number; simple: number; pro: number } | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    adminAPI.getTiers().then((res) => setLimits(res.data));
  }, []);

  const save = async () => {
    if (!limits) return;
    const res = await adminAPI.updateTiers(limits);
    setLimits(res.data);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (!limits) return null;

  return (
    <div className="bg-white rounded-2xl border p-4" style={{ borderColor: '#e3eee8' }}>
      <h2 className="font-semibold mb-4" style={{ color: '#0f3d2e' }}>
        Ліміти списків по тарифах
      </h2>
      <div className="space-y-3 max-w-[20rem]">
        {(['free', 'simple', 'pro'] as const).map((tier) => (
          <label key={tier} className="flex items-center justify-between gap-3">
            <span className="text-sm font-medium capitalize" style={{ color: '#33524a' }}>
              {tier}
            </span>
            <input
              type="number"
              min={1}
              value={limits[tier]}
              onChange={(e) => setLimits({ ...limits, [tier]: Number(e.target.value) })}
              className="w-24 px-3 py-2 border rounded-lg text-sm"
              style={{ borderColor: '#d0d9d5' }}
            />
          </label>
        ))}
      </div>
      <button
        onClick={save}
        className="mt-4 text-sm font-semibold rounded-lg"
        style={{ padding: '8px 16px', backgroundColor: saved ? '#d8f3e3' : '#0b6e4f', color: saved ? '#05603a' : 'white', border: 'none', cursor: 'pointer' }}
      >
        {saved ? '✓ Збережено' : 'Зберегти'}
      </button>
    </div>
  );
}

function UsersTab() {
  const [users, setUsers] = useState<UserRow[]>([]);

  const load = () => adminAPI.listUsers().then((res) => setUsers(res.data.users));

  useEffect(() => {
    load();
  }, []);

  const setTier = async (id: string, tier: string) => {
    await adminAPI.setUserTier(id, tier);
    load();
  };

  return (
    <div className="bg-white rounded-2xl border" style={{ borderColor: '#e3eee8' }}>
      <div className="p-4 border-b" style={{ borderColor: '#f0f0f0' }}>
        <h2 className="font-semibold" style={{ color: '#0f3d2e' }}>
          Юзери ({users.length})
        </h2>
      </div>
      <div className="divide-y" style={{ borderColor: '#f0f0f0' }}>
        {users.map((u) => (
          <div key={u.id} className="flex items-center gap-3 px-4 py-3">
            <span className="flex-1 text-sm" style={{ color: '#0f1419' }}>
              {u.email} {u.is_admin && <span style={{ color: '#0b6e4f' }}>(admin)</span>}
            </span>
            <select
              value={u.tier}
              onChange={(e) => setTier(u.id, e.target.value)}
              className="px-2 py-1.5 border rounded-lg text-sm"
              style={{ borderColor: '#d0d9d5' }}
            >
              <option value="free">free</option>
              <option value="simple">simple</option>
              <option value="pro">pro</option>
            </select>
          </div>
        ))}
      </div>
    </div>
  );
}