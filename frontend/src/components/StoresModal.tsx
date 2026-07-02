'use client';

interface StoresModalProps {
  isOpen: boolean;
  onClose: () => void;
  lang: 'ru' | 'uk' | 'en';
}

interface Store {
  name: string;
  url: string;
  color: string;
}

const STORES: Store[] = [
  {
    name: 'Aroma',
    url: 'https://aromamarketi.me/uvijek-svjeze/',
    color: '#e11d48',
  },
  {
    name: 'Voli',
    url: 'https://voli.me/',
    color: '#2563eb',
  },
  {
    name: 'HDL',
    url: 'https://www.digitalniletak.me/hd-lakovic',
    color: '#d97706',
  },
  {
    name: 'IDEA',
    url: 'https://www.idea.co.me/',
    color: '#0891b2',
  },
];

const translations = {
  ru: {
    title: 'Магазины',
    description: 'Магазины, где собираются цены товаров',
    store: 'Магазин',
    website: 'Веб-сайт',
    openWebsite: 'Открыть сайт',
  },
  uk: {
    title: 'Магазини',
    description: 'Магазини, звідки збираються ціни товарів',
    store: 'Магазин',
    website: 'Веб-сайт',
    openWebsite: 'Відкрити сайт',
  },
  en: {
    title: 'Stores',
    description: 'Stores from which product prices are collected',
    store: 'Store',
    website: 'Website',
    openWebsite: 'Open website',
  },
};

export function StoresModal({ isOpen, onClose, lang }: StoresModalProps) {
  const t = translations[lang];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[10000] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 p-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{t.title}</h2>
            <p className="text-sm text-gray-600 mt-1">{t.description}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Stores Table */}
        <div className="overflow-y-auto flex-1">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b-2 border-gray-200">
                <th className="text-left px-6 py-4 font-semibold text-gray-900">{t.store}</th>
                <th className="text-left px-6 py-4 font-semibold text-gray-900">{t.website}</th>
                <th className="text-center px-6 py-4 font-semibold text-gray-900">Action</th>
              </tr>
            </thead>
            <tbody>
              {STORES.map((store, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-6 h-6 rounded"
                        style={{ backgroundColor: store.color }}
                      ></div>
                      <span className="font-semibold text-gray-900">{store.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <a
                      href={store.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-brand-accent hover:underline break-all text-sm"
                    >
                      {store.url}
                    </a>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <a
                      href={store.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-4 py-2 bg-brand-accent text-white rounded-lg hover:bg-brand-deep transition-colors font-semibold text-sm"
                    >
                      🔗 {t.openWebsite}
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}