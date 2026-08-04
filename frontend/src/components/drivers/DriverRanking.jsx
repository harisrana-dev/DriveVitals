import { memo } from 'react';
import { Crown } from 'lucide-react';
import { useDriverRanking } from '../../hooks/useDrivers';
import { useSmoothValue } from '../../hooks/useSmoothValue';
import { getDriverTrend } from '../../utils/trend';

export const DriverRanking = memo(function DriverRanking({ onDriverClick }) {
  const rankings = useDriverRanking();
  const top3 = rankings.slice(0, 3);
  const bottom3 = rankings.slice(-3).reverse();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}
    >
      <div>
        <div
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: 'var(--color-text-muted)',
            marginBottom: 8,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <Crown size={14} style={{ color: 'var(--color-amber)' }} />
          Top Performers
        </div>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
          }}
        >
          {top3.map((d, i) => (
            <RankingRow key={d.id} driver={d} rank={i + 1} onClick={onDriverClick} />
          ))}
        </div>
      </div>

      <div>
        <div
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: 'var(--color-text-muted)',
            marginBottom: 8,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          Needs Improvement
        </div>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
          }}
        >
          {bottom3.map((d) => (
            <RankingRow key={d.id} driver={d} rank={rankings.indexOf(d) + 1} onClick={onDriverClick} />
          ))}
        </div>
      </div>
    </div>
  );
});

function RankingRow({ driver, rank, onClick }) {
  const trend = getDriverTrend(driver.score);
  const TrendIcon = trend.Icon;
  const smoothScore = useSmoothValue(driver.score);

  return (
    <div
      onClick={() => onClick && onClick(driver)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '8px 10px',
        borderRadius: 8,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'background 0.12s ease',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      <span
        style={{
          width: 22,
          fontSize: 11,
          fontWeight: 600,
          color: 'var(--color-text-muted)',
          fontVariantNumeric: 'tabular-nums',
          textAlign: 'center',
        }}
      >
        {rank}
      </span>
      <div
        style={{
          width: 26,
          height: 26,
          borderRadius: 7,
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
        {driver.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 13,
            fontWeight: 500,
            color: 'var(--color-text-primary)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {driver.name}
        </div>
        <div
          style={{
            fontSize: 11,
            color: 'var(--color-text-muted)',
          }}
        >
          {driver.tripsCompleted} trips
        </div>
      </div>
      <TrendIcon size={14} strokeWidth={2} style={{ color: trend.color, flexShrink: 0 }} />
      <span
        style={{
          fontSize: 16,
          fontWeight: 700,
          color: trend.color,
          fontVariantNumeric: 'tabular-nums',
          minWidth: 32,
          textAlign: 'right',
        }}
      >
        {Math.round(smoothScore)}
      </span>
    </div>
  );
}
