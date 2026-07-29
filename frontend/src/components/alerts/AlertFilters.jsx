import { memo } from 'react';
import { Search, Filter } from 'lucide-react';
import { useAlertFilters } from '../../hooks/useAlerts';
import { SEVERITIES, CATEGORIES, TIME_RANGES } from '../../utils/alerts';

const SEV_LABELS = { all: 'All', critical: 'Critical', warning: 'Warning', info: 'Information', resolved: 'Resolved' };
const CAT_LABELS = { all: 'All Categories', Driving: 'Driving', Engine: 'Engine', Fuel: 'Fuel', Cooling: 'Cooling', Electrical: 'Electrical' };
const TIME_LABELS = { live: 'Live', '1h': '1 Hour', today: 'Today', week: 'This Week', all: 'All Time' };

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
};

const btnActive = {
  background: 'var(--color-accent-subtle)',
  color: 'var(--color-accent)',
  borderColor: 'var(--color-accent)',
};

export const AlertFilters = memo(function AlertFilters() {
  const {
    filters, setSeverity, setCategory,
    setVehicleSearch, setDriverSearch, setTimeRange,
  } = useAlertFilters();

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
            {CAT_LABELS[c]}
          </button>
        ))}
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

      <div style={{ display: 'flex', gap: 8 }}>
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
      </div>
    </div>
  );
});
