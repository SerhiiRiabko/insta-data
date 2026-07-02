/**
 * TabSwitcher Component
 * Switch between Instagram and Official Sites
 */

'use client';

import { useTranslations } from 'next-intl';
import { useState } from 'react';

export type TabType = 'instagram' | 'official' | 'all';

interface TabSwitcherProps {
  onTabChange?: (tab: TabType) => void;
}

export function TabSwitcher({ onTabChange }: TabSwitcherProps) {
  const t = useTranslations();
  const [activeTab, setActiveTab] = useState<TabType>('all');

  const tabs: { id: TabType; label: string }[] = [
    { id: 'instagram', label: t('tabs.instagram') },
    { id: 'official', label: t('tabs.official') },
    { id: 'all', label: t('tabs.all') },
  ];

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    onTabChange?.(tab);
  };

  return (
    <div className="flex gap-2 flex-wrap">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => handleTabChange(tab.id)}
          className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
            activeTab === tab.id
              ? 'bg-primary-600 text-white shadow-lg'
              : 'bg-neutral-700 text-neutral-300 hover:bg-neutral-600'
          }`}
        >
          {tab.id === 'instagram' && '📸 '}
          {tab.id === 'official' && '🏪 '}
          {tab.id === 'all' && '📊 '}
          {tab.label}
        </button>
      ))}
    </div>
  );
}