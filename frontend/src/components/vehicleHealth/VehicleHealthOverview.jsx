import { memo } from 'react';
import { HealthKpiCards } from './HealthKpiCards';

export const VehicleHealthOverview = memo(function VehicleHealthOverview() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
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

      <HealthKpiCards />
    </div>
  );
});
