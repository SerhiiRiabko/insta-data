'use client';

import { useEffect, useState } from 'react';
import {
  adminAPI,
  authAPI,
  storesAPI,
  scraperAgentsAPI,
  type Access,
  type CurrentUser,
  type PlanSettings,
  type Plan,
  type StoreInput,
  type ScraperAgentInput,
} from '@/lib/api';
import { AuthModal } from '@/components/AuthModal';

interface StoreRow {
  id: string;
  name: string;
  initial: string;
  color: string;
  url: string;
  active: boolean;
  country: 'ME' | 'UA';
}

interface UserRow {
  id: string;
  email: string | null;
  telegram_id: number | null;
  telegram_username: string | null;
  label: string;
  is_admin: boolean;
  access: Access;
  compare_until: string | null;
  gold_until: string | null;
  created_at: string | null;
}

interface PaymentRequestRow {
  id: string;
  user: string;
  plan: Plan;
  amount_eur: number;
  comment: string;
  status: 'pending' | 'approved' | 'declined';
  created_at: string;
}

const PLAN_LABEL: Record<string, string> = { free: 'Безкоштовний', compare: 'Порівняння', gold: 'Gold' };

function untilLabel(value: string | null): string {
  if (!value) return '—';
  if (value === 'forever') return 'безстроково';
  const date = new Date(value);
  return date < new Date() ? `минув ${date.toLocaleDateString('uk-UA')}` : `до ${date.toLocaleDateString('uk-UA')}`;
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

const EMPTY_STORE: StoreInput = { name: '', initial: '', color: '#0b6e4f', url: '', active: true, country: 'ME' };
const COUNTRY_LABEL: Record<'ME' | 'UA', string> = { ME: '🇲🇪 Чорногорія', UA: '🇺🇦 Україна' };
const EMPTY_AGENT: ScraperAgentInput = { name: '', strategy: 'custom', store_ids: [], url: '', active: true };

export function AdminPageClient() {
  const [currentUser, setCurrentUser] = useState<CurrentUser | null | 'loading'>('loading');
  const [tab, setTab] = useState<'stores' | 'scrapers' | 'plans' | 'users' | 'payments'>('payments');

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
          onAuthenticated={(user) => setCurrentUser(user)}
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
          {currentUser.email || (currentUser.telegram?.username ? `@${currentUser.telegram.username}` : '')}
        </p>

        <div className="flex flex-wrap gap-1 mb-6 rounded-lg overflow-hidden border w-fit" style={{ borderColor: '#e3eee8' }}>
          {(['payments', 'users', 'plans', 'stores', 'scrapers'] as const).map((tb) => (
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
              {{ stores: 'Магазини', scrapers: 'Скрейпери', plans: 'Тарифи', users: 'Юзери', payments: 'Оплати' }[tb]}
            </button>
          ))}
        </div>

        {tab === 'stores' && <StoresTab />}
        {tab === 'scrapers' && <ScrapersTab />}
        {tab === 'plans' && <PlansTab />}
        {tab === 'users' && <UsersTab />}
        {tab === 'payments' && <PaymentsTab />}
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
    setForm({ name: s.name, initial: s.initial, color: s.color, url: s.url, active: s.active, country: s.country });
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
            <span className="text-xs flex-shrink-0" style={{ color: '#52736a' }}>
              {COUNTRY_LABEL[s.country] ?? s.country}
            </span>
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
            <select value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value as 'ME' | 'UA' })} className="px-3 py-2 border rounded-lg text-sm" style={{ borderColor: '#d0d9d5' }}>
              {Object.entries(COUNTRY_LABEL).map(([code, label]) => (
                <option key={code} value={code}>{label}</option>
              ))}
            </select>
            <input placeholder="URL сайту" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} className="px-3 py-2 border rounded-lg text-sm col-span-2" style={{ borderColor: '#d0d9d5' }} />
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

function PlansTab() {
  const [settings, setSettings] = useState<PlanSettings | null>(null);
  const [saved, setSaved] = useState(false);
  const [translations, setTranslations] = useState<Record<string, { total: number; running: boolean; translated: Record<string, number> }> | null>(null);

  const loadTranslations = () => adminAPI.translationStatus().then((res) => setTranslations(res.data));

  useEffect(() => {
    adminAPI.getPlanSettings().then((res) => setSettings(res.data));
    loadTranslations();
  }, []);

  const save = async () => {
    if (!settings) return;
    const res = await adminAPI.updatePlanSettings(settings);
    setSettings(res.data);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const fill = async (country: 'ME' | 'UA') => {
    await adminAPI.fillTranslations(country);
    loadTranslations();
  };

  if (!settings) return null;

  const numberField = (key: keyof PlanSettings, label: string, step = 1) => (
    <label key={key} className="flex items-center justify-between gap-3">
      <span className="text-sm" style={{ color: '#33524a' }}>
        {label}
      </span>
      <input
        type="number"
        min={step < 1 ? 0.5 : 1}
        step={step}
        value={settings[key] as number}
        onChange={(e) => setSettings({ ...settings, [key]: Number(e.target.value) })}
        className="w-28 px-3 py-2 border rounded-lg text-sm"
        style={{ borderColor: '#d0d9d5' }}
      />
    </label>
  );

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-2xl border p-4" style={{ borderColor: '#e3eee8' }}>
        <h2 className="font-semibold mb-1" style={{ color: '#0f3d2e' }}>
          Ціни тарифів (на місяць)
        </h2>
        <p className="text-xs mb-4" style={{ color: '#7d9a8d' }}>
          Порівняння — ціни всіх магазинів. Gold — порівняння + списки покупок і шеринг. Діють і на сайті, і в боті.
        </p>
        <div className="grid gap-3 sm:grid-cols-2 max-w-[36rem]">
          {numberField('compare_stars', 'Порівняння, ⭐')}
          {numberField('compare_eur', 'Порівняння, €', 0.5)}
          {numberField('gold_stars', 'Gold, ⭐')}
          {numberField('gold_eur', 'Gold, €', 0.5)}
          {numberField('gold_list_limit', 'Gold: макс. списків')}
        </div>

        <label className="block mt-4">
          <span className="text-sm font-medium" style={{ color: '#33524a' }}>
            Реквізити для оплати карткою
          </span>
          <span className="block text-xs mb-1" style={{ color: '#7d9a8d' }}>
            Номер картки / IBAN / отримувач — показується тим, хто платить переказом. Порожньо = оплата карткою вимкнена.
          </span>
          <textarea
            rows={3}
            value={settings.card_details}
            onChange={(e) => setSettings({ ...settings, card_details: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg text-sm"
            style={{ borderColor: '#d0d9d5', fontFamily: 'Space Grotesk, monospace' }}
          />
        </label>

        <button
          onClick={save}
          className="mt-3 text-sm font-semibold rounded-lg"
          style={{ padding: '8px 16px', backgroundColor: saved ? '#d8f3e3' : '#0b6e4f', color: saved ? '#05603a' : 'white', border: 'none', cursor: 'pointer' }}
        >
          {saved ? '✓ Збережено' : 'Зберегти'}
        </button>
      </div>

      <div className="bg-white rounded-2xl border p-4" style={{ borderColor: '#e3eee8' }}>
        <h2 className="font-semibold mb-1" style={{ color: '#0f3d2e' }}>
          Переклад назв товарів
        </h2>
        <p className="text-xs mb-3" style={{ color: '#7d9a8d' }}>
          Кеш → словник → Groq → Claude Haiku. Нові товари перекладаються автоматично після щотижневого оновлення цін.
        </p>
        {translations &&
          Object.entries(translations).map(([country, s]) => (
            <div key={country} className="flex items-center gap-3 py-2 flex-wrap" style={{ borderTop: '1px solid #f0f0f0' }}>
              <span className="text-sm font-medium w-28" style={{ color: '#0f1419' }}>
                {COUNTRY_LABEL[country as 'ME' | 'UA']}
              </span>
              <span className="text-xs flex-1" style={{ color: '#52736a' }}>
                {Object.entries(s.translated)
                  .map(([loc, n]) => `${loc}: ${n}/${s.total}`)
                  .join(' · ')}
              </span>
              <button
                onClick={() => fill(country as 'ME' | 'UA')}
                disabled={s.running}
                className="text-xs font-medium"
                style={{ color: s.running ? '#a3b5ae' : '#0b6e4f', background: 'none', border: 'none', cursor: s.running ? 'default' : 'pointer' }}
              >
                {s.running ? 'Перекладаємо…' : 'Перекласти відсутні'}
              </button>
            </div>
          ))}
        <button onClick={loadTranslations} className="text-xs mt-2" style={{ color: '#52736a', background: 'none', border: 'none', cursor: 'pointer' }}>
          ⟳ Оновити статус
        </button>
      </div>
    </div>
  );
}

function UsersTab() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [query, setQuery] = useState('');
  const [identifier, setIdentifier] = useState('');
  const [plan, setPlan] = useState<Plan>('gold');
  const [months, setMonths] = useState<string>('1');
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const load = (q = query) => adminAPI.listUsers(q).then((res) => setUsers(res.data.users));

  useEffect(() => {
    load('');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const grant = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      const res = await adminAPI.grant(identifier.trim(), plan, months === 'forever' ? null : Number(months));
      setMessage({
        ok: true,
        text: res.data.status === 'queued' ? res.data.message : `✓ ${res.data.user.label}: ${PLAN_LABEL[plan]} ${untilLabel(plan === 'gold' ? res.data.user.gold_until : res.data.user.compare_until)}`,
      });
      setIdentifier('');
      load();
    } catch (err: any) {
      setMessage({ ok: false, text: err?.response?.data?.detail || 'Помилка' });
    }
  };

  const revoke = async (id: string) => {
    await adminAPI.revoke(id, null);
    load();
  };

  return (
    <div className="space-y-4">
      <form onSubmit={grant} className="bg-white rounded-2xl border p-4" style={{ borderColor: '#e3eee8' }}>
        <h2 className="font-semibold mb-1" style={{ color: '#0f3d2e' }}>
          Видати тариф
        </h2>
        <p className="text-xs mb-3" style={{ color: '#7d9a8d' }}>
          Email, @нікнейм або числовий Telegram id. Незареєстрованому email тариф застосується при першому вході; Telegram-користувач має хоч раз запустити бота.
        </p>
        <div className="flex flex-wrap gap-2">
          <input
            required
            placeholder="email / @username / tg id"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            className="flex-1 min-w-[14rem] px-3 py-2 border rounded-lg text-sm"
            style={{ borderColor: '#d0d9d5' }}
          />
          <select value={plan} onChange={(e) => setPlan(e.target.value as Plan)} className="px-3 py-2 border rounded-lg text-sm" style={{ borderColor: '#d0d9d5' }}>
            <option value="gold">Gold</option>
            <option value="compare">Порівняння</option>
          </select>
          <select value={months} onChange={(e) => setMonths(e.target.value)} className="px-3 py-2 border rounded-lg text-sm" style={{ borderColor: '#d0d9d5' }}>
            <option value="1">1 місяць</option>
            <option value="3">3 місяці</option>
            <option value="6">6 місяців</option>
            <option value="12">12 місяців</option>
            <option value="forever">Безстроково</option>
          </select>
          <button type="submit" className="text-sm font-semibold rounded-lg" style={{ padding: '8px 16px', backgroundColor: '#0b6e4f', color: 'white', border: 'none', cursor: 'pointer' }}>
            Видати
          </button>
        </div>
        {message && (
          <p className="text-sm mt-2" style={{ color: message.ok ? '#05603a' : '#dc2626' }}>
            {message.text}
          </p>
        )}
      </form>

      <div className="bg-white rounded-2xl border" style={{ borderColor: '#e3eee8' }}>
        <div className="p-4 border-b flex items-center gap-3 flex-wrap" style={{ borderColor: '#f0f0f0' }}>
          <h2 className="font-semibold" style={{ color: '#0f3d2e' }}>
            Юзери ({users.length})
          </h2>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              load();
            }}
            className="flex-1 flex justify-end"
          >
            <input
              placeholder="Пошук: email або @нік"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full max-w-[16rem] px-3 py-1.5 border rounded-lg text-sm"
              style={{ borderColor: '#d0d9d5' }}
            />
          </form>
        </div>
        <div className="divide-y" style={{ borderColor: '#f0f0f0' }}>
          {users.map((u) => (
            <div key={u.id} className="flex items-center gap-3 px-4 py-3 flex-wrap">
              <span className="flex-1 min-w-[12rem] text-sm break-all" style={{ color: '#0f1419' }}>
                {u.label} {u.is_admin && <span style={{ color: '#0b6e4f' }}>(admin)</span>}
              </span>
              <span className="text-xs" style={{ color: u.access.plan === 'free' ? '#a3b5ae' : '#05603a' }}>
                {PLAN_LABEL[u.access.plan]}
                {u.access.plan === 'gold' && !u.is_admin && ` · ${untilLabel(u.gold_until)}`}
                {u.access.plan === 'compare' && ` · ${untilLabel(u.compare_until)}`}
              </span>
              {!u.is_admin && u.access.plan !== 'free' && (
                <button onClick={() => revoke(u.id)} className="text-xs font-medium" style={{ color: '#dc2626', background: 'none', border: 'none', cursor: 'pointer' }}>
                  Забрати
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PaymentsTab() {
  const [requests, setRequests] = useState<PaymentRequestRow[]>([]);
  const [status, setStatus] = useState<'pending' | 'all'>('pending');
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = (s = status) => adminAPI.paymentRequests(s).then((res) => setRequests(res.data.requests));

  useEffect(() => {
    load(status);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  const decide = async (id: string, decision: 'approve' | 'decline') => {
    setBusyId(id);
    try {
      await adminAPI.decidePayment(id, decision);
    } finally {
      setBusyId(null);
      load();
    }
  };

  const STATUS: Record<string, string> = { pending: 'Очікує', approved: '✅ Підтверджено', declined: '❌ Відхилено' };

  return (
    <div className="bg-white rounded-2xl border" style={{ borderColor: '#e3eee8' }}>
      <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: '#f0f0f0' }}>
        <h2 className="font-semibold" style={{ color: '#0f3d2e' }}>
          Оплати карткою
        </h2>
        <select value={status} onChange={(e) => setStatus(e.target.value as 'pending' | 'all')} className="px-2 py-1.5 border rounded-lg text-sm" style={{ borderColor: '#d0d9d5' }}>
          <option value="pending">Очікують</option>
          <option value="all">Усі</option>
        </select>
      </div>
      <p className="text-xs px-4 pt-3" style={{ color: '#7d9a8d' }}>
        Ті самі запити приходять у Telegram з кнопками, якщо ваш Telegram прив’язаний до цього акаунта або ваш нік — @adyvan_2008. Оплата зірками зараховується автоматично.
      </p>
      {requests.length === 0 ? (
        <p className="text-sm p-4" style={{ color: '#a3b5ae' }}>
          Немає запитів.
        </p>
      ) : (
        <div className="divide-y" style={{ borderColor: '#f0f0f0' }}>
          {requests.map((r) => (
            <div key={r.id} className="flex items-center gap-3 px-4 py-3 flex-wrap">
              <div className="flex-1 min-w-[14rem]">
                <div className="text-sm break-all" style={{ color: '#0f1419' }}>
                  {r.user}
                </div>
                <div className="text-xs" style={{ color: '#52736a' }}>
                  {PLAN_LABEL[r.plan]} · {r.amount_eur} € · {new Date(r.created_at).toLocaleString('uk-UA')}
                  {r.comment && ` · ${r.comment}`}
                </div>
              </div>
              {r.status === 'pending' ? (
                <>
                  <button
                    onClick={() => decide(r.id, 'approve')}
                    disabled={busyId === r.id}
                    className="text-xs font-semibold rounded-lg"
                    style={{ padding: '6px 12px', backgroundColor: '#0b6e4f', color: 'white', border: 'none', cursor: 'pointer' }}
                  >
                    Підтвердити
                  </button>
                  <button
                    onClick={() => decide(r.id, 'decline')}
                    disabled={busyId === r.id}
                    className="text-xs font-medium"
                    style={{ color: '#dc2626', background: 'none', border: 'none', cursor: 'pointer' }}
                  >
                    Відхилити
                  </button>
                </>
              ) : (
                <span className="text-xs" style={{ color: '#52736a' }}>
                  {STATUS[r.status]}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
