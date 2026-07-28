import { useVehicles } from '../../hooks/useFleetData';

const categoryStyles = {
  healthy: { bg: 'var(--color-green-bg)', color: 'var(--color-green)', label: 'Healthy' },
  monitor: { bg: 'var(--color-amber-bg)', color: 'var(--color-amber)', label: 'Monitor' },
  attention: { bg: 'var(--color-red-bg)', color: 'var(--color-red)', label: 'Attention' },
  critical: { bg: 'var(--color-red-light)', color: 'var(--color-red)', label: 'Critical' },
};

export function FleetHealthMatrix() {
  const vehicles = useVehicles();

  return (
    <div className="fade-in stagger-5" style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 12,
      padding: 20,
    }}>
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 2 }}>
          Fleet Health Matrix
        </h3>
        <p style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
          Vehicle health scores at a glance
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
        gap: 8,
      }}>
        {vehicles.map((v) => {
          const cat = categoryStyles[v.healthCategory];
          const barColor = v.healthScore >= 85 ? 'var(--color-green)'
            : v.healthScore >= 70 ? 'var(--color-amber)'
            : 'var(--color-red)';

          return (
            <div
              key={v.id}
              style={{
                padding: '12px',
                borderRadius: 8,
                border: `1px solid ${v.healthCategory === 'attention' || v.healthCategory === 'critical' ? barColor : 'var(--color-border-light)'}`,
                background: v.healthCategory === 'attention' || v.healthCategory === 'critical' ? `${barColor}08` : 'var(--color-bg)',
                transition: 'all 0.15s ease',
                cursor: 'default',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = barColor;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = v.healthCategory === 'attention' || v.healthCategory === 'critical' ? barColor : 'var(--color-border-light)';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)' }}>{v.id}</span>
                <span style={{
                  fontSize: 9,
                  fontWeight: 600,
                  padding: '1px 5px',
                  borderRadius: 3,
                  background: cat.bg,
                  color: cat.color,
                  textTransform: 'uppercase',
                }}>
                  {cat.label}
                </span>
              </div>

              <div style={{ fontSize: 22, fontWeight: 700, color: barColor, marginBottom: 8, lineHeight: 1 }}>
                {v.healthScore}
              </div>

              <div style={{ height: 3, borderRadius: 2, background: 'var(--color-border)', overflow: 'hidden' }}>
                <div style={{
                  width: `${v.healthScore}%`,
                  height: '100%',
                  borderRadius: 2,
                  background: barColor,
                  transition: 'width 0.3s ease',
                }} />
              </div>

              <div style={{ marginTop: 8, fontSize: 11, color: 'var(--color-text-muted)' }}>
                {v.status === 'active' ? v.name : v.status.charAt(0).toUpperCase() + v.status.slice(1)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
