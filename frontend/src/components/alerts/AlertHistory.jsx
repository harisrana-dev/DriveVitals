import { memo, useState } from 'react';
import { AlertStatusTabs } from './AlertStatusTabs';
import { AlertFilters } from './AlertFilters';
import { AlertHistoryTable } from './AlertHistoryTable';

/**
 * Alert History: a self-contained operational workspace. The section frame
 * owns the title, description, status tabs, filters bar and table, so the
 * whole block reads as one surface — separate from the intelligence panel
 * above and LIVE NOW. It consumes the lifted filter API from the page, so
 * the tabs, KPI strip and table all stay in sync.
 */
export const AlertHistory = memo(function AlertHistory({
  filtersApi,
  onIncidentClick,
  selectedKey,
}) {
  const [sortBy, setSortBy] = useState('severity');

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            Alert History
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>
            Inspect and manage fleet alert records.
          </div>
        </div>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap' }}>
          {filtersApi.resultLabel}
        </span>
      </div>

      <AlertStatusTabs
        counts={filtersApi.activeTabCounts}
        activeTab={filtersApi.filters.statusTab}
        onTabChange={filtersApi.setStatusTab}
      />
      <AlertFilters filtersApi={filtersApi} />
      <AlertHistoryTable
        incidents={filtersApi.filteredIncidents}
        onIncidentClick={onIncidentClick}
        selectedKey={selectedKey}
        sortBy={sortBy}
        onSortChange={setSortBy}
      />
    </div>
  );
});
