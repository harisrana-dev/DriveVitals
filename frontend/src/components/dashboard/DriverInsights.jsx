import { TrendingUp, TrendingDown, Minus, ArrowRight } from 'lucide-react';
import { useTopDrivers } from '../../hooks/useFleetData';
import { Link } from 'react-router-dom';

const trendIcons = {
  improving: <TrendingUp size={13} />,
  stable: <Minus size={13} />,
  declining: <TrendingDown size={13} />,
};

const trendColors = {
  improving: 'var(--color-green)',
  stable: 'var(--color-text-muted)',
  declining: 'var(--color-red)',
};

export function DriverInsights() {
  const topDrivers = useTopDrivers(5);

  return (
    <div className="fade-in stagger-5" style={{
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
            Driver Insights
          </h3>
          <p style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            Top performing drivers this period
          </p>
        </div>
        <Link
          to="/drivers"
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
        {topDrivers.map((driver, i) => (
          <div
            key={driver.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 20px',
              borderBottom: i < topDrivers.length - 1 ? '1px solid var(--color-border-light)' : 'none',
            }}
          >
            <div style={{
              width: 28,
              height: 28,
              borderRadius: 8,
              background: 'var(--color-accent-subtle)',
              color: 'var(--color-accent)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 11,
              fontWeight: 700,
              flexShrink: 0,
            }}>
              {i + 1}
            </div>

            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-text-primary)' }}>
                {driver.name}
              </div>
              <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                {driver.tripsCompleted} trips \u00b7 {driver.id}
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
              <div style={{ width: 48 }}>
                <div style={{ height: 4, borderRadius: 2, background: 'var(--color-border)', overflow: 'hidden' }}>
                  <div style={{
                    width: `${driver.safetyScore}%`,
                    height: '100%',
                    borderRadius: 2,
                    background: driver.safetyScore >= 90 ? 'var(--color-green)' : driver.safetyScore >= 75 ? 'var(--color-amber)' : 'var(--color-red)',
                  }} />
                </div>
              </div>
              <span style={{
                fontSize: 13,
                fontWeight: 600,
                color: driver.safetyScore >= 90 ? 'var(--color-green)' : driver.safetyScore >= 75 ? 'var(--color-amber)' : 'var(--color-red)',
                fontVariantNumeric: 'tabular-nums',
                minWidth: 28,
                textAlign: 'right',
              }}>
                {driver.safetyScore}
              </span>
              <span style={{ color: trendColors[driver.trend] }}>
                {trendIcons[driver.trend]}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
