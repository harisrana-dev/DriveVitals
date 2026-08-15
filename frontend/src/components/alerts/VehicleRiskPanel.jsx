import { memo } from 'react';
import { Gauge } from 'lucide-react';

const GRID = '1.5fr 1.1fr 56px 78px 52px 1.1fr';

export const VehicleRiskPanel = memo(function VehicleRiskPanel({ vehicles, onViewVehicle }) {
  const list = Array.isArray(vehicles) ? vehicles : [];
  const maxRisk = Math.max(...list.map((v) => v.riskScore), 1);

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
          Vehicle Risk
        </span>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 4 }}>
          {list.length} active {list.length === 1 ? 'vehicle' : 'vehicles'}
        </span>
      </div>
      <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 10 }}>
        Active alerts, severity-weighted (critical 5 · high 4 · medium 2 · low 1)
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
        <span style={{ textAlign: 'right' }}>Active</span>
        <span style={{ textAlign: 'right' }}>Crit/High</span>
        <span style={{ textAlign: 'right' }}>Risk</span>
        <span>Category</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {list.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '8px 4px' }}>
            No vehicles with active alerts.
          </div>
        ) : (
          list.slice(0, 6).map((v) => (
            <RiskRow
              key={v.vehicle_id}
              vehicle={v}
              maxRisk={maxRisk}
              onViewVehicle={onViewVehicle}
            />
          ))
        )}
      </div>
    </div>
  );
});

function RiskRow({ vehicle, maxRisk, onViewVehicle }) {
  const barWidth = Math.max(6, (vehicle.riskScore / maxRisk) * 100);
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onViewVehicle && onViewVehicle(vehicle.vehicle_id)}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && onViewVehicle) {
          e.preventDefault();
          onViewVehicle(vehicle.vehicle_id);
        }
      }}
      style={{
        display: 'grid',
        gridTemplateColumns: GRID,
        gap: 8,
        alignItems: 'center',
        padding: '7px 4px',
        borderRadius: 8,
        cursor: onViewVehicle ? 'pointer' : 'default',
        transition: 'background-color 0.12s ease',
      }}
      onMouseEnter={(e) => { if (onViewVehicle) e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
      onMouseLeave={(e) => { if (onViewVehicle) e.currentTarget.style.background = 'transparent'; }}
    >
      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {vehicle.vehicle_name}
      </span>
      <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {vehicle.driver_name || '—'}
      </span>
      <span style={{ fontSize: 11, fontWeight: 600, textAlign: 'right', color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
        {vehicle.activeCount}
      </span>
      <span style={{ fontSize: 11, textAlign: 'right', color: vehicle.criticalHighCount > 0 ? 'var(--color-red)' : 'var(--color-text-muted)', fontWeight: vehicle.criticalHighCount > 0 ? 600 : 400, fontVariantNumeric: 'tabular-nums' }}>
        {vehicle.criticalHighCount}
      </span>
      <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4 }}>
        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
          {vehicle.riskScore}
        </span>
        <span
          style={{
            width: 26,
            height: 3,
            borderRadius: 2,
            background: 'var(--color-border-light)',
            overflow: 'hidden',
          }}
        >
          <span
            style={{
              display: 'block',
              height: '100%',
              width: `${barWidth}%`,
              background: vehicle.riskScore >= 9 ? 'var(--color-red)' : vehicle.riskScore >= 5 ? 'var(--color-amber)' : 'var(--color-accent)',
            }}
          />
        </span>
      </span>
      <span style={{ fontSize: 10, color: 'var(--color-text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {vehicle.dominantCategory || '—'}
      </span>
    </div>
  );
}
