import { memo, useMemo } from 'react';
import { useAlerts } from '../../hooks/useAlerts';
import { healthColor } from '../../utils/health';

export const MostActiveVehicles = memo(function MostActiveVehicles() {
  const { incidents } = useAlerts();

  const vehicles = useMemo(() => {
    const map = {};
    incidents.forEach((a) => {
      if (!map[a.vehicle_id]) {
        map[a.vehicle_id] = { vehicle_id: a.vehicle_id, vehicle_name: a.vehicle_name, incidentCount: 0, health: a.overall_health_score ?? 100 };
      }
      map[a.vehicle_id].incidentCount++;
    });
    return Object.values(map).sort((a, b) => b.incidentCount - a.incidentCount).slice(0, 5);
  }, [incidents]);

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
        Most Affected Vehicles
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {vehicles.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            No incidents.
          </div>
        ) : (
          vehicles.map((v) => {
            const color = healthColor(v.health >= 80 ? 'healthy' : v.health >= 50 ? 'warning' : 'critical');
            return (
              <div
                key={v.vehicle_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '8px 10px',
                  borderRadius: 8,
                  background: 'var(--color-bg)',
                }}
              >
                <div
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 6,
                    background: 'var(--color-accent-subtle)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--color-accent)',
                    fontSize: 10,
                    fontWeight: 600,
                    flexShrink: 0,
                  }}
                >
                  {v.vehicle_name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-primary)' }}>
                    {v.vehicle_name}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                    {v.incidentCount}
                  </span>
                  <span style={{ fontSize: 11, color, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                    {Math.round(v.health)}%
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
});
