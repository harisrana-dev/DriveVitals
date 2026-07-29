import { memo } from 'react';
import { DollarSign, TrendingUp, AlertCircle } from 'lucide-react';
import { useMaintenance } from '../../hooks/useMaintenance';

export const FleetMaintenanceCost = memo(function FleetMaintenanceCost() {
  const { fleetCost } = useMaintenance();

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 14 }}>
        Estimated Fleet Cost
      </div>
      <div
        style={{
          fontSize: 11,
          color: 'var(--color-text-muted)',
          fontStyle: 'italic',
          marginBottom: 12,
        }}
      >
        Estimated
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <CostRow
          icon={<DollarSign size={14} strokeWidth={1.8} />}
          label="Monthly Estimate"
          value={fleetCost.monthly}
          color="var(--color-accent)"
        />
        <CostRow
          icon={<TrendingUp size={14} strokeWidth={1.8} />}
          label="Upcoming Estimate"
          value={fleetCost.upcoming}
          color="var(--color-amber)"
        />
        <CostRow
          icon={<AlertCircle size={14} strokeWidth={1.8} />}
          label="Critical Estimate"
          value={fleetCost.critical}
          color="var(--color-red)"
        />
      </div>
    </div>
  );
});

function CostRow({ icon, label, value, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: 6,
          background: 'var(--color-surface-hover)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color,
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{label}</div>
      </div>
      <span
        style={{
          fontSize: 13,
          fontWeight: 600,
          color: 'var(--color-text-primary)',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        ${value.toLocaleString()}
      </span>
    </div>
  );
}
