'use client';

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
  lang: 'ru' | 'uk' | 'en';
}

const translations = {
  ru: {
    title: 'О проекте',
    mission: 'Миссия',
    missionText:
      'Помочь жителям Черногории сэкономить деньги, сравнивая цены товаров в 4 главных магазинах страны.',
    features: 'Особенности',
    feature1: 'Сравнение цен в реальном времени',
    feature2: '4 магазина: Aroma, Voli, HDL, IDEA',
    feature3: '3 языка: Украинский, Русский, Черногорский',
    feature4: 'Список покупок с расчетом оптимального магазина',
    techStack: 'Технологический стек',
    frontend: 'Frontend: Next.js 15 + React 19 + Tailwind 4',
    backend: 'Backend: FastAPI + MongoDB + PostgreSQL',
    scrapers: 'Парсинг: Playwright + BeautifulSoup4',
  },
  uk: {
    title: 'Про проект',
    mission: 'Мета',
    missionText:
      'Допомогти мешканцям Чорногорії заощадити гроші, порівнюючи ціни товарів у 4 головних магазинах країни.',
    features: 'Особливості',
    feature1: 'Порівняння цін у реальному часі',
    feature2: '4 магазини: Aroma, Voli, HDL, IDEA',
    feature3: '3 мови: Українська, Російська, Чорногорська',
    feature4: 'Список покупок з розрахунком оптимального магазину',
    techStack: 'Технічний стек',
    frontend: 'Frontend: Next.js 15 + React 19 + Tailwind 4',
    backend: 'Backend: FastAPI + MongoDB + PostgreSQL',
    scrapers: 'Парсинг: Playwright + BeautifulSoup4',
  },
  en: {
    title: 'About',
    mission: 'Mission',
    missionText:
      'Help residents of Montenegro save money by comparing product prices across 4 major stores in the country.',
    features: 'Features',
    feature1: 'Real-time price comparison',
    feature2: '4 stores: Aroma, Voli, HDL, IDEA',
    feature3: '3 languages: Ukrainian, Russian, Montenegrin',
    feature4: 'Shopping list with optimal store calculation',
    techStack: 'Technology Stack',
    frontend: 'Frontend: Next.js 15 + React 19 + Tailwind 4',
    backend: 'Backend: FastAPI + MongoDB + PostgreSQL',
    scrapers: 'Scraping: Playwright + BeautifulSoup4',
  },
};

export function AboutModal({ isOpen, onClose, lang }: AboutModalProps) {
  const t = translations[lang];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[10000] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="border-b border-gray-200 p-6 flex items-center justify-between sticky top-0 bg-white">
          <h2 className="text-2xl font-bold text-gray-900">{t.title}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Mission */}
          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">{t.mission}</h3>
            <p className="text-gray-700 leading-relaxed">{t.missionText}</p>
          </section>

          {/* Features */}
          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">{t.features}</h3>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start gap-2">
                <span className="text-brand-accent font-bold">✓</span>
                <span>{t.feature1}</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-brand-accent font-bold">✓</span>
                <span>{t.feature2}</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-brand-accent font-bold">✓</span>
                <span>{t.feature3}</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-brand-accent font-bold">✓</span>
                <span>{t.feature4}</span>
              </li>
            </ul>
          </section>

          {/* Tech Stack */}
          <section>
            <h3 className="text-lg font-bold text-gray-900 mb-3">{t.techStack}</h3>
            <ul className="space-y-2 text-sm text-gray-700 font-mono bg-gray-50 p-4 rounded-lg">
              <li>{t.frontend}</li>
              <li>{t.backend}</li>
              <li>{t.scrapers}</li>
            </ul>
          </section>

          {/* Footer */}
          <div className="border-t border-gray-200 pt-4 text-center text-xs text-gray-500">
            <p>💰 PriceCompare — 2026</p>
          </div>
        </div>
      </div>
    </div>
  );
}