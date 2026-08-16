import { memo } from 'react';
import { Gauge } from 'lucide-react';

const RISK_LEVEL_META = {
  critical: { label: 'Critical', color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
  high: { label: 'High', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  medium: { label: 'Medium', color: 'var(--color-blue)', bg: 'var(--color-blue-bg)' },
  good: { label: 'Good', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
};

const GRID = '1.4fr 1fr 0.7fr 0.7fr 0.8fr 0.9fr 0.8fr';

function healthColor(score) {
  if (score == null) return 'var(--color-text-muted)';
  if (score >= 80) return 'var(--color-green)';
  if (score >= 50) return 'var(--color-amber)';
  return 'var(--color-red)';
}

export const VehicleMaintenanceRiskPanel = memo(function VehicleMaintenanceRiskPanel({ vehicles, onOpenVehicle }) {
  const list = Array.isArray(vehicles) ? vehicles : [];

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
        flex: 1,
        minWidth: 0,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
        <Gauge size={14} style={{ color: 'var(--color-amber)' }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
          Vehicle Maintenance Risk
        </span>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 4 }}>
          {list.length} {list.length === 1 ? 'vehicle' : 'vehicles'} with pending work
        </span>
      </div>
      <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 10 }}>
        Ranked by worst service status (critical → overdue · high → due soon · medium → scheduled)
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: GRID,
          gap: 8,
          padding: '0 4px 6px',
          fontSize: 10,
          fontWeight: 600,
          color: 'var(--color-text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        <span>Vehicle</span>
        <span>Driver</span>
        <span style={{ textAlign: 'right' }}>Health</span>
        <span style={{ textAlign: 'right' }}>Overdue</span>
        <span style={{ textAlign: 'right' }}>Due Soon</span>
        <span style={{ textAlign: 'right' }}>Actionable</span>
        <span>Level</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {list.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '8px 4px' }}>
            No vehicles with pending maintenance work.
          </div>
        ) : (
          list.slice(0, 6).map((v) => (
            <RiskRow key={v.vehicle_id} vehicle={v} onOpenVehicle={onOpenVehicle} />
          ))
        )}
      </div>
    </div>
  );
});

function RiskRow({ vehicle, onOpenVehicle }) {
  const level = RISK_LEVEL_META[vehicle.level] || RISK_LEVEL_META.good;
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onOpenVehicle && onOpenVehicle(vehicle.vehicle_id)}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && onOpenVehicle) {
          e.preventDefault();
          onOpenVehicle(vehicle.vehicle_id);
        }
      }}
      style={{
        display: 'grid',
        gridTemplateColumns: GRID,
        gap: 8,
        alignItems: 'center',
        padding: '7px 4px',
        borderRadius: 8,
        cursor: onOpenVehicle ? 'pointer' : 'default',
        transition: 'background-color 0.12s ease',
      }}
      onMouseEnter={(e) => { if (onOpenVehicle) e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
      onMouseLeave={(e) => { if (onOpenVehicle) e.currentTarget.style.background = 'transparent'; }}
    >
      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {vehicle.vehicle_name}
      </span>
      <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {vehicle.driver_name || '\u2014'}
      </span>
      <span style={{ fontSize: 11, fontWeight: 600, textAlign: 'right', color: healthColor(vehicle.overall_health_score), fontVariantNumeric: 'tabular-nums' }}>
        {vehicle.overall_health_score != null ? `${Math.round(vehicle.overall_health_score)}%` : '\u2014'}
      </span>
      <span style={{ fontSize: 11, textAlign: 'right', color: vehicle.overdue > 0 ? 'var(--color-red)' : 'var(--color-text-muted)', fontWeight: vehicle.overdue > 0 ? 600 : 400, fontVariantNumeric: 'tabular-nums' }}>
        {vehicle.overdue}
      </span>
      <span style={{ fontSize: 11, textAlign: 'right', color: vehicle.dueSoon > 0 ? 'var(--color-amber)' : 'var(--color-text-muted)', fontWeight: vehicle.dueSoon > 0 ? 600 : 400, fontVariantNumeric: 'tabular-nums' }}>
        {vehicle.dueSoon}
      </span>
      <span style={{ fontSize: 11, fontWeight: 700, textAlign: 'right', color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
        {vehicle.actionable}
      </span>
      <span
        style={{
          justifySelf: 'start',
          padding: '2px 8px',
          borderRadius: 4,
          background: level.bg,
          color: level.color,
          fontSize: 10,
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        {level.label}
      </span>
    </div>
  );
}
