import { memo } from 'react';
import { PriorityBadge } from './PriorityBadge';
import { DueBadge } from './DueBadge';
import { serviceIcon } from '../../utils/maintenance';
import { HealthBar } from '../vehicleHealth/HealthBar';

export const ServiceCard = memo(function ServiceCard({ item, onClick }) {
  const icon = serviceIcon(item.serviceType);

  return (
    <div
      onClick={() => onClick && onClick(item)}
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: '14px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.15s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--color-accent)';
        e.currentTarget.style.boxShadow = 'var(--color-shadow-sm)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--color-border)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 0 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: 'var(--color-accent-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 14,
              flexShrink: 0,
            }}
          >
            {icon}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                {item.vehicleName}
              </span>
              <PriorityBadge priority={item.priority} />
            </div>
            <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
              {item.driverName}
            </div>
          </div>
        </div>
        <div style={{ flexShrink: 0 }}>
          <DueBadge status={item.dueStatus} />
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 12, color: 'var(--color-text-primary)', fontWeight: 500 }}>
          {item.serviceType}
        </span>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
          {item.remainingKm > 0 ? `Due in ${item.remainingKm.toLocaleString()} km` : 'Due immediately'}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
          <span style={{ color: 'var(--color-text-muted)' }}>Vehicle Health</span>
          <span style={{ color: 'var(--color-text-secondary)', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>
            {Math.round(item.health)}%
          </span>
        </div>
        <HealthBar score={item.health} height={5} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
          {item.vehicleId}
        </span>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
          {item.odometer.toLocaleString()} km
        </span>
      </div>
    </div>
  );
});
