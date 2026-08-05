import { memo } from 'react';
import { MaintenanceKpiCards } from './MaintenanceKpiCards';

export const MaintenanceOverview = memo(function MaintenanceOverview() {
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
          Maintenance
        </h1>
        <p
          style={{
            fontSize: 13,
            color: 'var(--color-text-secondary)',
          }}
        >
          Fleet maintenance planning and service operations
        </p>
      </div>
      <MaintenanceKpiCards />
    </div>
  );
});
