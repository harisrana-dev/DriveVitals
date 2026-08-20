import { memo } from 'react';
import { Truck } from 'lucide-react';
import { useDashboard } from '../../hooks/useDashboard';
import { useVehicleDrawer } from '../../context/useVehicleDrawer';
import { useRelativeTime } from '../../hooks/useRelativeTime';
import { healthLabel, healthColor } from '../../utils/health';

const STATUS_META = {
  ACTIVE: { label: 'Active', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
  TRIP_COMPLETED: { label: 'Trip Completed', color: 'var(--color-purple)', bg: 'var(--color-purple-bg)' },
  IDLE: { label: 'Idle', color: 'var(--color-blue)', bg: 'var(--color-blue-bg)' },
  STALE: { label: 'Stale', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  OFFLINE: { label: 'Offline', color: 'var(--color-text-muted)', bg: 'var(--color-surface-hover)' },
};

const GRID = '1.3fr 1fr 110px 120px 56px 56px 64px 1fr';

function subtitleFor(connState) {
  switch (connState) {
    case 'live':
      return 'Real-time telemetry reported by the fleet';
    case 'stale':
      return 'Showing last known telemetry \u2014 live data is stale';
    case 'offline':
      return 'Showing last known telemetry \u2014 live data unavailable';
    case 'syncing':
      return 'Syncing fleet data\u2026';
    default:
      return 'Connecting to live fleet telemetry\u2026';
  }
}

/**
 * Full fleet table. Every telemetry column renders "—" when the backend
 * has no value; unknown is never drawn as zero. Rows open the vehicle
 * drawer. The subtitle is connection-aware so stale data is labelled.
 */
export const LiveFleetTable = memo(function LiveFleetTable() {
  const { vehicles, connState } = useDashboard();
  const { openDrawer } = useVehicleDrawer();
  const list = Array.isArray(vehicles) ? vehicles : [];

  return (
    <div
      className="fade-in"
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '14px 20px',
          borderBottom: '1px solid var(--color-border-light)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Truck size={14} style={{ color: 'var(--color-accent)' }} />
          <div>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Live Fleet
            </span>
            <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 6 }}>
              {list.length} {list.length === 1 ? 'vehicle' : 'vehicles'}
            </span>
          </div>
        </div>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
          {subtitleFor(connState)}
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: GRID,
          gap: 8,
          padding: '8px 20px 6px',
          fontSize: 10,
          fontWeight: 600,
          color: 'var(--color-text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
          borderBottom: '1px solid var(--color-border-light)',
        }}
      >
        <span>Vehicle</span>
        <span>Driver</span>
        <span>Status</span>
        <span>Health</span>
        <span style={{ textAlign: 'right' }}>Speed</span>
          <span style={{ textAlign: 'right' }}>Fuel Level</span>
        <span style={{ textAlign: 'right' }}>Coolant</span>
        <span>Updated</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {list.length === 0 ? (
          <div style={{ padding: '22px 20px', textAlign: 'center', fontSize: 12, color: 'var(--color-text-muted)' }}>
            No fleet data available.
          </div>
        ) : (
          list.map((v) => (
            <FleetRow
              key={v.id}
              vehicle={v}
              last={false}
              onOpen={() => openDrawer({ id: v.id })}
            />
          ))
        )}
      </div>
    </div>
  );
});

function FleetRow({ vehicle, onOpen }) {
  const timeAgo = useRelativeTime(vehicle.lastUpdate);
  const status = STATUS_META[vehicle.displayStatus] || STATUS_META.OFFLINE;
  const healthCat = vehicle.healthCategory || 'unavailable';
  const healthLabelText = healthLabel(healthCat);

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`Open ${vehicle.name}`}
      className="row-focusable"
      onClick={onOpen}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && onOpen) {
          e.preventDefault();
          onOpen();
        }
      }}
      style={{
        display: 'grid',
        gridTemplateColumns: GRID,
        gap: 8,
        alignItems: 'center',
        padding: '9px 20px',
        borderBottom: '1px solid var(--color-border-light)',
        cursor: 'pointer',
        transition: 'background-color 0.12s ease',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {vehicle.name}
      </span>
      <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {vehicle.driver || '—'}
      </span>
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2px 7px',
          borderRadius: 5,
          background: status.bg,
          color: status.color,
          fontSize: 10,
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
          whiteSpace: 'nowrap',
          width: 'fit-content',
        }}
      >
        {status.label}
      </span>
      <span style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
        <span
          style={{
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: healthColor(healthCat),
            flexShrink: 0,
          }}
        />
        <span
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: healthCat === 'unavailable' ? 'var(--color-text-muted)' : 'var(--color-text-primary)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {healthLabelText}
        </span>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
          {vehicle.healthScore == null ? '' : vehicle.healthScore}
        </span>
      </span>
      <CellValue value={vehicle.speed} unit="km/h" />
      <CellValue value={vehicle.fuelLevel} unit="%" />
      <CellValue value={vehicle.coolantTemp} unit={' \u00B0C'} />
      <span style={{ fontSize: 10, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap' }}>
        {vehicle.lastUpdate ? timeAgo : '\u2014'}
      </span>
    </div>
  );
}

function CellValue({ value, unit }) {
  return (
    <span style={{ fontSize: 11, color: value == null ? 'var(--color-text-muted)' : 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums', textAlign: 'right', whiteSpace: 'nowrap' }}>
      {value == null ? '\u2014' : `${value} ${unit}`}
    </span>
  );
}
