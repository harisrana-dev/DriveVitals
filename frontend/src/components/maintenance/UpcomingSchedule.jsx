import { memo } from 'react';
import { useMaintenance } from '../../hooks/useMaintenance';

export const UpcomingSchedule = memo(function UpcomingSchedule() {
  const { upcomingSchedule } = useMaintenance();

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
        Upcoming Schedule
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
        {upcomingSchedule.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '8px 0' }}>
            No upcoming services scheduled.
          </div>
        ) : (
          upcomingSchedule.map((group) => (
            <div key={group.label}>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: 'var(--color-text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  padding: '8px 0 4px',
                  borderTop: '1px solid var(--color-border-light)',
                }}
              >
                {group.label}
              </div>
              {group.items.map((item) => (
                <div
                  key={item.vehicleId + item.serviceType}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '6px 0',
                  }}
                >
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background:
                        item.priority === 'critical' ? 'var(--color-red)' :
                        item.priority === 'due' ? 'var(--color-amber)' :
                        'var(--color-green)',
                      flexShrink: 0,
                    }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, color: 'var(--color-text-primary)', fontWeight: 500 }}>
                      {item.vehicleName}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                      {item.serviceType}
                    </div>
                  </div>
                  <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                    {item.daysUntilDue === 0 ? 'Today' : `${item.daysUntilDue}d`}
                  </span>
                </div>
              ))}
            </div>
          ))
        )}
      </div>
    </div>
  );
});
