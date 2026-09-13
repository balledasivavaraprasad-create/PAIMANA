import React from 'react';

export interface TabOption<T extends string> {
  id: T;
  label: string;
  count?: number;
  icon?: React.ReactNode;
}

interface SectionTabsProps<T extends string> {
  tabs: TabOption<T>[];
  activeTab: T;
  onChange: (tabId: T) => void;
  size?: 'sm' | 'md';
  className?: string;
}

export function SectionTabs<T extends string>({
  tabs,
  activeTab,
  onChange,
  size = 'md',
  className = '',
}: SectionTabsProps<T>) {
  return (
    <div className={`flex items-center gap-1.5 p-1 rounded-xl bg-[var(--surface-sunken)] border border-[var(--border-hairline)] ${className}`}>
      {tabs.map(tab => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={`flex items-center gap-2 rounded-lg font-medium transition-all cursor-pointer ${
              size === 'sm' ? 'px-3 py-1 text-xs' : 'px-4 py-2 text-xs'
            } ${
              isActive
                ? 'bg-[var(--accent)] text-white shadow-sm font-semibold'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--glass-bg)]'
            }`}
          >
            {tab.icon && <span className="opacity-90">{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span
                className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                  isActive
                    ? 'bg-white/20 text-white'
                    : 'bg-[var(--border-hairline)] text-[var(--text-muted)]'
                }`}
              >
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

export default SectionTabs;
