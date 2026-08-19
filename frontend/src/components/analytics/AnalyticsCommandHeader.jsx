import { memo } from 'react';
import { Calendar, Filter, RefreshCw } from 'lucide-react';

const selectStyle = {
  padding: '6px 10px',
  borderRadius: 8,
  border: '1px solid var(--color-border)',
  background: 'var(--color-surface)',
  color: 'var(--color-text-primary)',
  fontSize: 12,
  fontWeight: 500,
  cursor: 'pointer',
  outline: 'none',
  fontFamily: 'inherit',
};

const btnStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: 5,
  padding: '6px 12px',
  borderRadius: 8,
  border: '1px solid var(--color-border)',
  background: 'var(--color-surface)',
  color: 'var(--color-text-secondary)',
  fontSize: 12,
  fontWeight: 500,
  cursor: 'pointer',
  fontFamily: 'inherit',
};

export const AnalyticsCommandHeader = memo(function AnalyticsCommandHeader({
  range,
  setRange,
  customStart,
  setCustomStart,
  customEnd,
  setCustomEnd,
  vehicleFilter,
  setVehicleFilter,
  driverFilter,
  setDriverFilter,
  vehicles,
  drivers,
  loading,
  onRefresh,
  presets,
}) {
  return (
    <div
      className="fade-in"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 10,
        padding: '16px 20px',
        borderRadius: 14,
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--color-text-secondary)' }}>
          <Calendar size={15} strokeWidth={1.8} />
          <span style={{ fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Date Range
          </span>
        </div>

        <select
          value={range}
          onChange={(e) => setRange(e.target.value)}
          style={selectStyle}
        >
          {(presets || []).map((p) => (
            <option key={p.key} value={p.key}>{p.label}</option>
          ))}
        </select>

        {range === 'custom' && (
          <>
            <input
              type="date"
              value={customStart}
              onChange={(e) => setCustomStart(e.target.value)}
              style={{ ...selectStyle, width: 140 }}
            />
            <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>to</span>
            <input
              type="date"
              value={customEnd}
              onChange={(e) => setCustomEnd(e.target.value)}
              style={{ ...selectStyle, width: 140 }}
            />
          </>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--color-text-secondary)' }}>
          <Filter size={14} strokeWidth={1.8} />
        </div>

        <select
          value={vehicleFilter}
          onChange={(e) => setVehicleFilter(e.target.value)}
          style={{ ...selectStyle, minWidth: 130 }}
        >
          <option value="">All Vehicles</option>
          {(vehicles || []).map((v) => (
            <option key={v.vehicle_id} value={v.vehicle_id}>
              {v.registration_number || v.vehicle_id}
            </option>
          ))}
        </select>

        <select
          value={driverFilter}
          onChange={(e) => setDriverFilter(e.target.value)}
          style={{ ...selectStyle, minWidth: 130 }}
        >
          <option value="">All Drivers</option>
          {(drivers || []).map((d) => (
            <option key={d.driver_id} value={d.driver_id}>
              {d.first_name} {d.last_name}
            </option>
          ))}
        </select>

        <button
          onClick={onRefresh}
          disabled={loading}
          style={{
            ...btnStyle,
            cursor: loading ? 'default' : 'pointer',
          }}
        >
          <RefreshCw
            size={13}
            strokeWidth={1.8}
            style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }}
          />
          Refresh
        </button>
      </div>
    </div>
  );
});
