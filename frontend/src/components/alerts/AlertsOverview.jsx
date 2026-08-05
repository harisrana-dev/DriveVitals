import { memo } from 'react';
import { AlertKpiCards } from './AlertKpiCards';

export const AlertsOverview = memo(function AlertsOverview() {
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
          Alerts
        </h1>
        <p
          style={{
            fontSize: 13,
            color: 'var(--color-text-secondary)',
          }}
        >
          Real-time fleet incident monitoring and operational response
        </p>
      </div>
      <AlertKpiCards />
    </div>
  );
});
