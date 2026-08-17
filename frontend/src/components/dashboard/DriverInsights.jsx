import { memo } from 'react';
import { TrendingUp, TrendingDown, Minus, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useDriverRanking, useDrivers } from '../../hooks/useDrivers';
import { EmptyState } from '../ui/EmptyState';
import { driverRankingQuality } from '../../utils/dashboard';

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

const EMPTY_CONFIG = {
  'no-data': {
    title: 'No driver scores yet',
    description: 'Driver safety scores will appear once backend driver statistics are available.',
  },
  degraded: {
    title: 'Driver scoring is insufficient',
    description: 'Safety scores are currently too low to be meaningful for ranking. Data may still be collecting or calibrating.',
  },
};

/**
 * Driver performance list. Labeled "Driver performance" (never "this
 * period" — the data is all-time). When backend driver statistics are
 * absent or implausibly low, a data-quality state is shown instead of
 * ranking garbage. Rows navigate to the Drivers page.
 */
export const DriverInsights = memo(function DriverInsights() {
  const drivers = useDrivers();
  const rankings = useDriverRanking();
  const quality = driverRankingQuality(drivers);
  const topDrivers = rankings.slice(0, 5);
  const empty = EMPTY_CONFIG[quality];

  return (
    <div
      className="fade-in"
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--color-border-light)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 2 }}>
            Driver Insights
          </h3>
          <p style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            {quality === 'ok'
              ? 'Driver performance across the fleet'
              : empty?.description || 'Driver performance'}
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

      {quality !== 'ok' ? (
        <div style={{ padding: 20 }}>
          <EmptyState
            title={empty?.title || 'Driver scoring unavailable'}
            description={empty?.description || 'No driver safety scores are available for ranking yet.'}
            action={
              <Link
                to="/drivers"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '6px 12px',
                  borderRadius: 8,
                  background: 'var(--color-accent)',
                  color: '#fff',
                  fontSize: 12,
                  fontWeight: 600,
                  textDecoration: 'none',
                  transition: 'opacity 0.15s ease',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.85'; }}
                onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
              >
                View drivers <ArrowRight size={12} />
              </Link>
            }
          />
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {topDrivers.map((driver, i) => (
            <Link
              key={driver.id}
              to="/drivers"
              className="row-focusable"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 20px',
                borderBottom: i < topDrivers.length - 1 ? '1px solid var(--color-border-light)' : 'none',
                textDecoration: 'none',
                transition: 'background-color 0.12s ease',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
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
                  {driver.tripsCompleted == null ? 'No trips' : `${driver.tripsCompleted} trips`} · {driver.id}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                <div style={{ width: 48 }}>
                  <div style={{ height: 4, borderRadius: 2, background: 'var(--color-border)', overflow: 'hidden' }}>
                    <div style={{
                      width: `${driver.score}%`,
                      height: '100%',
                      borderRadius: 2,
                      background: driver.score >= 90 ? 'var(--color-green)' : driver.score >= 75 ? 'var(--color-amber)' : 'var(--color-red)',
                    }} />
                  </div>
                </div>
                <span style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: driver.score >= 90 ? 'var(--color-green)' : driver.score >= 75 ? 'var(--color-amber)' : 'var(--color-red)',
                  fontVariantNumeric: 'tabular-nums',
                  minWidth: 28,
                  textAlign: 'right',
                }}>
                  {driver.score}
                </span>
                {driver.trend && (
                  <span style={{ color: trendColors[driver.trend] }}>
                    {trendIcons[driver.trend]}
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
});
