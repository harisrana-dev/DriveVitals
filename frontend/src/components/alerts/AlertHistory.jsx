import { memo, useState } from 'react';
import { AlertsSectionTitle } from './AlertsSectionTitle';
import { AlertStatusTabs } from './AlertStatusTabs';
import { AlertFilters } from './AlertFilters';
import { AlertHistoryTable } from './AlertHistoryTable';

/**
 * Alert History: status tabs, filters bar and the incident table. The
 * whole block consumes the lifted filter API from the page, so the tabs,
 * KPI strip and table all stay in sync.
 */
export const AlertHistory = memo(function AlertHistory({
  filtersApi,
  onIncidentClick,
  selectedKey,
}) {
  const [sortBy, setSortBy] = useState('severity');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <AlertsSectionTitle
        title="Alert History"
        right={<span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{filtersApi.resultLabel}</span>}
      />
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
