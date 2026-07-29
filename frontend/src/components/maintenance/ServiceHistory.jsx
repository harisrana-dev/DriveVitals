import { memo } from 'react';
import { useMaintenance } from '../../hooks/useMaintenance';

export const ServiceHistory = memo(function ServiceHistory() {
  const { serviceHistory } = useMaintenance();

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
        Service History
        <span style={{ fontSize: 11, fontWeight: 400, color: 'var(--color-text-muted)', marginLeft: 8 }}>
          Recent
        </span>
      </div>
      <div
        style={{
          maxHeight: 300,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 0,
        }}
      >
        {serviceHistory.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '12px 0' }}>
            No service history available.
          </div>
        ) : (
          serviceHistory.map((entry, i) => (
            <div
              key={entry.id}
              style={{
                display: 'flex',
                gap: 12,
                padding: '10px 0',
                borderBottom: i < serviceHistory.length - 1 ? '1px solid var(--color-border-light)' : 'none',
              }}
            >
              <div
                style={{
                  width: 2,
                  borderRadius: 1,
                  background: 'var(--color-accent)',
                  flexShrink: 0,
                  marginTop: 4,
                }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                    {entry.serviceType}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                    {entry.date}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
                  {entry.vehicleName}
                </div>
                <div style={{ display: 'flex', gap: 16, marginTop: 2 }}>
                  <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                    {entry.mileage.toLocaleString()} km
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                    ${entry.cost}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                    {entry.technician}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
});
