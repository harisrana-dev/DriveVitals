import { memo } from 'react';
import { ArrowRight, Wrench, AlertTriangle, Clock, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useMaintenanceItems } from '../../hooks/useFleetData';

const priorityStyles = {
  critical: { bg: 'var(--color-red-bg)', color: 'var(--color-red)', icon: <AlertTriangle size={14} />, label: 'Critical' },
  upcoming: { bg: 'var(--color-amber-bg)', color: 'var(--color-amber)', icon: <Clock size={14} />, label: 'Upcoming' },
  monitor: { bg: 'var(--color-surface-hover)', color: 'var(--color-text-muted)', icon: <CheckCircle size={14} />, label: 'Monitor' },
};

export const MaintenanceQueue = memo(function MaintenanceQueue() {
  const items = useMaintenanceItems();

  return (
    <div className="fade-in stagger-6" style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 12,
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--color-border-light)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 2 }}>
            Maintenance Queue
          </h3>
          <p style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            {items.length} items requiring attention
          </p>
        </div>
        <Link
          to="/maintenance"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            fontSize: 12,
            color: 'var(--color-accent)',
            fontWeight: 500,
            textDecoration: 'none',
            transition: 'opacity 0.15s ease',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.7'; }}
          onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
        >
          View all <ArrowRight size={13} />
        </Link>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {items.map((item, i) => {
          const ps = priorityStyles[item.priority];
          return (
            <div
              key={item.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '14px 20px',
                borderBottom: i < items.length - 1 ? '1px solid var(--color-border-light)' : 'none',
              }}
            >
              <div style={{
                width: 34,
                height: 34,
                borderRadius: 8,
                background: ps.bg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: ps.color,
                flexShrink: 0,
              }}>
                <Wrench size={16} />
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                    {item.vehicleId}
                  </span>
                  <span style={{
                    fontSize: 10,
                    fontWeight: 600,
                    padding: '1px 5px',
                    borderRadius: 3,
                    background: ps.bg,
                    color: ps.color,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}>
                    {ps.label}
                  </span>
                </div>
                <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 2 }}>
                  {item.type}
                </div>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                  {item.dueDistance !== undefined && item.dueDistance > 0 && `Due in ${item.dueDistance} km`}
                  {item.dueDistance !== undefined && item.dueDistance === 0 && 'Immediate'}
                  {item.dueDate && item.dueDistance === undefined && `Due in ${item.dueDate}`}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: ps.color }}>
                {ps.icon}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});
