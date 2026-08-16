import { memo } from 'react';
import { Search, Filter, RotateCcw } from 'lucide-react';
import { MAINTENANCE_TYPE_LABELS } from '../../utils/maintenance';

const PRIORITY_OPTIONS = [
  { key: 'all', label: 'All' },
  { key: 'critical', label: 'Critical' },
  { key: 'high', label: 'High' },
  { key: 'medium', label: 'Medium' },
  { key: 'low', label: 'Low' },
];

const btnBase = {
  padding: '5px 10px',
  borderRadius: 6,
  fontSize: 11,
  fontWeight: 500,
  border: '1px solid var(--color-border)',
  background: 'transparent',
  color: 'var(--color-text-secondary)',
  cursor: 'pointer',
  transition: 'all 0.12s ease',
  lineHeight: 1,
  fontFamily: 'inherit',
};

const btnActive = {
  background: 'var(--color-accent-subtle)',
  color: 'var(--color-accent)',
  borderColor: 'var(--color-accent)',
};

/**
 * Filters bar. Pure presentational: reads the lifted filter API from the
 * page and calls its setters, so the state is shared with the KPI strip,
 * tabs and work queue. Priority and service type filter the canonical work
 * items; the search boxes filter by vehicle and driver.
 */
export const MaintenanceFilters = memo(function MaintenanceFilters({ filtersApi }) {
  const {
    filters,
    setPriority,
    setType,
    setVehicleSearch,
    setDriverSearch,
    resetFilters,
  } = filtersApi;

  const isDefault =
    filters.statusTab === 'all' &&
    !filters.dueWithin2000 &&
    filters.priority === 'all' &&
    filters.type === 'all' &&
    filters.vehicleSearch === '' &&
    filters.driverSearch === '';

  return (
    <div
      style={{
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border-light)',
        borderRadius: 10,
        padding: '10px 14px',
        display: 'flex',
        flexWrap: 'wrap',
        gap: 12,
        alignItems: 'center',
      }}
    >
      <Filter size={14} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginRight: 4 }}>Priority</span>
        {PRIORITY_OPTIONS.map((o) => (
          <button
            key={o.key}
            onClick={() => setPriority(o.key)}
            style={{ ...btnBase, ...(filters.priority === o.key ? btnActive : {}) }}
          >
            {o.label}
          </button>
        ))}
      </div>

      <div style={{ width: 1, height: 20, background: 'var(--color-border)', flexShrink: 0 }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginRight: 4 }}>Type</span>
        <button
          onClick={() => setType('all')}
          style={{ ...btnBase, ...(filters.type === 'all' ? btnActive : {}) }}
        >
          All
        </button>
        {Object.entries(MAINTENANCE_TYPE_LABELS).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setType(filters.type === key ? 'all' : key)}
            style={{ ...btnBase, ...(filters.type === key ? btnActive : {}) }}
          >
            {label}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, minWidth: 120 }} />

      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            padding: '4px 8px',
            borderRadius: 6,
            border: '1px solid var(--color-border)',
            background: 'transparent',
          }}
        >
          <Search size={12} style={{ color: 'var(--color-text-muted)' }} />
          <input
            placeholder="Search vehicle..."
            value={filters.vehicleSearch}
            onChange={(e) => setVehicleSearch(e.target.value)}
            style={{
              border: 'none',
              background: 'transparent',
              outline: 'none',
              fontSize: 11,
              color: 'var(--color-text-primary)',
              width: 110,
              fontFamily: 'inherit',
            }}
          />
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            padding: '4px 8px',
            borderRadius: 6,
            border: '1px solid var(--color-border)',
            background: 'transparent',
          }}
        >
          <Search size={12} style={{ color: 'var(--color-text-muted)' }} />
          <input
            placeholder="Search driver..."
            value={filters.driverSearch}
            onChange={(e) => setDriverSearch(e.target.value)}
            style={{
              border: 'none',
              background: 'transparent',
              outline: 'none',
              fontSize: 11,
              color: 'var(--color-text-primary)',
              width: 110,
              fontFamily: 'inherit',
            }}
          />
        </div>
        {!isDefault && (
          <button
            onClick={resetFilters}
            title="Reset filters"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              padding: '5px 10px',
              borderRadius: 6,
              border: '1px solid var(--color-border)',
              background: 'transparent',
              color: 'var(--color-text-muted)',
              fontSize: 11,
              fontWeight: 500,
              cursor: 'pointer',
              fontFamily: 'inherit',
              lineHeight: 1,
              transition: 'all 0.12s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--color-text-primary)';
              e.currentTarget.style.background = 'var(--color-surface-hover)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--color-text-muted)';
              e.currentTarget.style.background = 'transparent';
            }}
          >
            <RotateCcw size={12} />
            Reset
          </button>
        )}
      </div>
    </div>
  );
});
