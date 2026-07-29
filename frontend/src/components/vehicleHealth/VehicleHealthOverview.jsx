import { memo } from 'react';
import { HealthKpiCards } from './HealthKpiCards';
import { useVehicleHealth } from '../../hooks/useVehicleHealth';

export const VehicleHealthOverview = memo(function VehicleHealthOverview() {
  const { fleetStats } = useVehicleHealth();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              marginBottom: 4,
            }}
          >
            Vehicle Health
          </h1>
          <p
            style={{
              fontSize: 13,
              color: 'var(--color-text-secondary)',
            }}
          >
            Monitor vehicle condition, detect risks, and prevent unexpected downtime.
          </p>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 11,
            color: 'var(--color-text-muted)',
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: fleetStats ? 'var(--color-green)' : 'var(--color-text-muted)',
              flexShrink: 0,
            }}
          />
          {fleetStats ? `Live · ${fleetStats.total} vehicles` : 'Connecting...'}
        </div>
      </div>

      <HealthKpiCards />
    </div>
  );
});
