import { memo } from 'react';
import { useMaintenance } from '../../hooks/useMaintenance';
import { ServiceCard } from './ServiceCard';

export const ServiceQueue = memo(function ServiceQueue({ onServiceClick }) {
  const { serviceQueue } = useMaintenance();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div
        style={{
          fontSize: 13,
          fontWeight: 600,
          color: 'var(--color-text-primary)',
          marginBottom: 4,
        }}
      >
        Service Queue
        <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--color-text-muted)', marginLeft: 8 }}>
          {serviceQueue.length} vehicles
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {serviceQueue.length === 0 ? (
          <div
            style={{
              padding: 24,
              textAlign: 'center',
              fontSize: 13,
              color: 'var(--color-text-muted)',
              background: 'var(--color-surface)',
              borderRadius: 12,
              border: '1px solid var(--color-border)',
            }}
          >
            All vehicles are in good condition. No services required.
          </div>
        ) : (
          serviceQueue.map((item) => (
            <ServiceCard key={item.id} item={item} onClick={onServiceClick} />
          ))
        )}
      </div>
    </div>
  );
});
