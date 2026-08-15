import { memo } from 'react';
import { Search, Filter, RotateCcw } from 'lucide-react';
import { SEVERITIES, CATEGORIES, TIME_RANGES } from '../../utils/alerts';
import { categoryLabel } from '../../services/alertAdapter';

const SEV_LABELS = {
  all: 'All',
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  info: 'Info',
};
const CAT_LABELS = {
  all: 'All Categories',
  safety_driving: 'Safety & Driving',
  vehicle_health: 'Vehicle Health',
  cooling: 'Cooling',
  fuel: 'Fuel',
  engine: 'Engine',
  electrical: 'Electrical',
  transmission: 'Transmission',
  brakes: 'Brakes',
  maintenance: 'Maintenance',
  trip: 'Trip',
  other: 'Other',
};
const TIME_LABELS = {
  live: 'Live',
  '1h': '1 Hour',
  today: 'Today',
  '7d': '7 Days',
  '30d': '30 Days',
  all: 'All Time',
};

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
 * tabs and table. Unclassified is a first-class filter value for the
 * legacy NULL-category alerts.
 */
export const AlertFilters = memo(function AlertFilters({ filtersApi }) {
  const {
    filters, setSeverity, setCategory,
    setVehicleSearch, setDriverSearch, setTimeRange,
  } = filtersApi;

  const isDefault =
    filters.severity === 'all' &&
    filters.category === 'all' &&
    filters.vehicleSearch === '' &&
    filters.driverSearch === '' &&
    filters.timeRange === 'all' &&
    filters.statusTab === 'active' &&
    !filters.unacknowledgedOnly &&
    !filters.resolvedWithinH;

  const handleReset = () => {
    setSeverity('all');
    setCategory('all');
    setVehicleSearch('');
    setDriverSearch('');
    setTimeRange('all');
  };

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: '12px 16px',
        display: 'flex',
        flexWrap: 'wrap',
        gap: 12,
        alignItems: 'center',
      }}
    >
      <Filter size={14} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginRight: 4 }}>Severity</span>
        {SEVERITIES.map((s) => (
          <button
            key={s}
            onClick={() => setSeverity(s)}
            style={{ ...btnBase, ...(filters.severity === s ? btnActive : {}) }}
          >
            {SEV_LABELS[s]}
          </button>
        ))}
      </div>

      <div style={{ width: 1, height: 20, background: 'var(--color-border)', flexShrink: 0 }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginRight: 4 }}>Category</span>
        {CATEGORIES.map((c) => (
          <button
            key={c}
            onClick={() => setCategory(filters.category === c ? 'all' : c)}
            style={{ ...btnBase, ...(filters.category === c ? btnActive : {}) }}
          >
            {CAT_LABELS[c] || categoryLabel(c)}
          </button>
        ))}
        <button
          onClick={() => setCategory(filters.category === '__unclassified__' ? 'all' : '__unclassified__')}
          style={{
            ...btnBase,
            ...(filters.category === '__unclassified__' ? btnActive : {}),
            fontStyle: filters.category === '__unclassified__' ? 'normal' : 'italic',
            color: filters.category === '__unclassified__' ? 'var(--color-accent)' : 'var(--color-text-muted)',
          }}
        >
          Unclassified
        </button>
      </div>

      <div style={{ width: 1, height: 20, background: 'var(--color-border)', flexShrink: 0 }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginRight: 4 }}>Time</span>
        {TIME_RANGES.map((t) => (
          <button
            key={t}
            onClick={() => setTimeRange(t)}
            style={{ ...btnBase, ...(filters.timeRange === t ? btnActive : {}) }}
          >
            {TIME_LABELS[t]}
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
              width: 100,
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
              width: 100,
              fontFamily: 'inherit',
            }}
          />
        </div>
        {!isDefault && (
          <button
            onClick={handleReset}
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
