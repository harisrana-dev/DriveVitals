import { memo, useState } from 'react';
import { MaintenanceStatusTabs } from './MaintenanceStatusTabs';
import { MaintenanceFilters } from './MaintenanceFilters';
import { MaintenanceTable } from './MaintenanceTable';

/**
 * Service Work Queue: the operational workspace for pending maintenance.
 * The section frame owns the title, description, status tabs, filters bar
 * and table so the block reads as one surface. It consumes the lifted
 * filter API from the page, so the KPI strip, tabs and table stay in sync.
 */
export const ServiceWorkQueue = memo(function ServiceWorkQueue({
  filtersApi,
  onOpenVehicle,
}) {
  const [sortBy, setSortBy] = useState('status');

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
            Service Work Queue
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>
            Pending maintenance across the fleet.
          </div>
        </div>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap' }}>
          {filtersApi.resultLabel}
        </span>
      </div>

      <MaintenanceStatusTabs
        counts={filtersApi.activeTabCounts}
        activeTab={filtersApi.filters.statusTab}
        onTabChange={filtersApi.setStatusTab}
      />
      <MaintenanceFilters filtersApi={filtersApi} />
      <MaintenanceTable
        workItems={filtersApi.sortedByStatus}
        onOpenVehicle={onOpenVehicle}
        sortBy={sortBy}
        onSortChange={setSortBy}
      />
    </div>
  );
});
