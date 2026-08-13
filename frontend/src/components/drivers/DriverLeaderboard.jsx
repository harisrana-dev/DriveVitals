import { memo, useMemo, useState } from 'react';
import {
  ArrowUpDown, TrendingUp, TrendingDown, Minus, ChevronRight,
} from 'lucide-react';
import {
  driverRiskLevel,
  leadingBehaviour,
} from '../../services/driverAdapter';
import { DriverRiskBadge } from './DriverRiskBadge';

const STATUS_META = {
  active: { label: 'ACTIVE', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
  off_duty: { label: 'OFF DUTY', color: 'var(--color-text-muted)', bg: 'var(--color-bg)' },
  offline: { label: 'OFFLINE', color: 'var(--color-text-muted)', bg: 'var(--color-bg)' },
};

const TREND_META = {
  improving: { Icon: TrendingUp, color: 'var(--color-green)' },
  declining: { Icon: TrendingDown, color: 'var(--color-red)' },
  stable: { Icon: Minus, color: 'var(--color-text-muted)' },
};

function gradeColor(grade) {
  if (!grade) return 'var(--color-text-muted)';
  if (grade === 'A') return 'var(--color-green)';
  if (grade === 'B') return 'var(--color-accent)';
  if (grade === 'C' || grade === 'D') return 'var(--color-amber)';
  return 'var(--color-red)';
}

function scoreColor(score) {
  if (score == null) return 'var(--color-text-muted)';
  if (score >= 90) return 'var(--color-green)';
  if (score >= 70) return 'var(--color-amber)';
  return 'var(--color-red)';
}

function formatKm(km) {
  if (km == null) return '—';
  if (km >= 1000) return `${(km / 1000).toFixed(1)}k km`;
  return `${Math.round(km)} km`;
}

const SORTERS = {
  name: (d) => d.name.toLowerCase(),
  status: (d) => d.status,
  vehicle: (d) => (d.vehicleName || d.vehicleId || '').toLowerCase(),
  historical: (d) => d.historical?.safetyScore ?? -1,
  live: (d) => d.live?.score ?? -1,
  risk: (d) => riskRank(driverRiskLevel(d)),
  trips: (d) => d.historical?.tripsCompleted ?? -1,
  distance: (d) => d.historical?.totalDistanceKm ?? -1,
  trend: (d) => trendRank(d.historical?.trend),
};

function riskRank(level) {
  if (level === 'critical') return 0;
  if (level === 'high') return 1;
  if (level === 'moderate') return 2;
  if (level === 'low') return 3;
  return 4;
}

function trendRank(trend) {
  if (trend === 'improving') return 0;
  if (trend === 'stable') return 1;
  if (trend === 'declining') return 2;
  return 3;
}

function SortableHeader({ label, column, align = 'left', sortKey, onSort }) {
  const active = sortKey === column;
  return (
    <div
      onClick={() => onSort(column)}
      style={{
        display: 'flex',
        alignItems: align === 'right' ? 'flex-end' : 'center',
        justifyContent: align === 'right' ? 'flex-end' : 'flex-start',
        gap: 4,
        cursor: 'pointer',
        userSelect: 'none',
        color: active ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
        fontWeight: active ? 700 : 600,
        fontSize: 10,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        whiteSpace: 'nowrap',
      }}
    >
      {label}
      <ArrowUpDown size={10} style={{ opacity: active ? 1 : 0.4, flexShrink: 0 }} />
    </div>
  );
}

export const DriverLeaderboard = memo(function DriverLeaderboard({ drivers, onDriverClick }) {
  const [sortKey, setSortKey] = useState('historical');
  const [sortDir, setSortDir] = useState('desc');

  const sorted = useMemo(() => {
    const sorter = SORTERS[sortKey] || SORTERS.historical;
    const rows = [...drivers].sort((a, b) => {
      const av = sorter(a);
      const bv = sorter(b);
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return rows.map((d, i) => ({ driver: d, rank: i + 1 }));
  }, [drivers, sortKey, sortDir]);

  const handleSort = (key) => {
    if (key === sortKey) {
      setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir(key === 'name' || key === 'vehicle' ? 'asc' : 'desc');
    }
  };

  if (drivers.length === 0) {
    return (
      <div
        style={{
          fontSize: 12,
          color: 'var(--color-text-muted)',
          padding: '8px 2px',
        }}
      >
        No drivers match the current filters.
      </div>
    );
  }

  const SortableHeaderColumn = (label, column, align) => (
    <SortableHeader
      label={label}
      column={column}
      align={align}
      sortKey={sortKey}
      onSort={handleSort}
    />
  );

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '44px 1.6fr 1fr 1.3fr 0.9fr 0.9fr 1fr 0.7fr 0.9fr 0.9fr 1.2fr 34px',
          gap: 8,
          alignItems: 'center',
          padding: '10px 16px',
          borderBottom: '1px solid var(--color-border)',
          background: 'var(--color-bg)',
        }}
      >
        <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>#</span>
        {SortableHeaderColumn('Driver', 'name')}
        {SortableHeaderColumn('Status', 'status')}
        {SortableHeaderColumn('Vehicle', 'vehicle')}
        {SortableHeaderColumn('Hist. Safety', 'historical', 'right')}
        {SortableHeaderColumn('Live Score', 'live', 'right')}
        {SortableHeaderColumn('Risk', 'risk')}
        {SortableHeaderColumn('Trips', 'trips', 'right')}
        {SortableHeaderColumn('Distance', 'distance', 'right')}
        {SortableHeaderColumn('Trend', 'trend')}
        <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Key Event</span>
        <span />
      </div>

      {sorted.map(({ driver, rank }) => (
        <LeaderboardRow
          key={driver.id}
          driver={driver}
          rank={rank}
          onClick={onDriverClick}
        />
      ))}

      {drivers.length >= 6 && (
        <div
          style={{
            padding: '8px 16px',
            fontSize: 11,
            color: 'var(--color-text-muted)',
            borderTop: '1px solid var(--color-border-light)',
          }}
        >
          {drivers.length} drivers ranked by {sortKey === 'historical' ? 'historical safety score' : sortKey} (
          {sortDir === 'asc' ? 'ascending' : 'descending'})
        </div>
      )}
    </div>
  );
});

function LeaderboardRow({ driver, rank, onClick }) {
  const status = STATUS_META[driver.status] || STATUS_META.offline;
  const hist = driver.historical || {};
  const live = driver.live || {};
  const trend = hist.trend ? TREND_META[hist.trend] : null;
  const TrendIcon = trend ? trend.Icon : null;
  const riskLevel = driverRiskLevel(driver);
  const keyEvent = leadingBehaviour(driver);

  return (
    <div
      onClick={() => onClick && onClick(driver)}
      style={{
        display: 'grid',
        gridTemplateColumns: '44px 1.6fr 1fr 1.3fr 0.9fr 0.9fr 1fr 0.7fr 0.9fr 0.9fr 1.2fr 34px',
        gap: 8,
        alignItems: 'center',
        padding: '10px 16px',
        borderBottom: '1px solid var(--color-border-light)',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'background 0.1s ease',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      <span
        style={{
          fontSize: 12,
          fontWeight: 700,
          color: rank <= 3 ? 'var(--color-amber)' : 'var(--color-text-muted)',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {rank}
      </span>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: 8,
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
          {driver.initials}
        </div>
        <div style={{ minWidth: 0 }}>
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
              fontSize: 10,
              color: 'var(--color-text-muted)',
              fontFamily: 'monospace',
            }}
          >
            {driver.id}
          </div>
        </div>
      </div>

      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 5,
          padding: '2px 8px',
          borderRadius: 6,
          background: status.bg,
          color: status.color,
          fontSize: 10,
          fontWeight: 600,
          letterSpacing: '0.02em',
          lineHeight: 1,
          width: 'fit-content',
        }}
      >
        <span
          style={{
            width: 5,
            height: 5,
            borderRadius: '50%',
            background: status.color,
            flexShrink: 0,
          }}
        />
        {status.label}
      </span>

      <div style={{ minWidth: 0 }}>
        <div
          style={{
            fontSize: 12,
            fontWeight: 500,
            color: 'var(--color-text-primary)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {driver.vehicleName || '—'}
        </div>
        {driver.vehicleId && (
          <div
            style={{
              fontSize: 10,
              color: 'var(--color-text-muted)',
              fontFamily: 'monospace',
            }}
          >
            {driver.vehicleId}
          </div>
        )}
      </div>

      <div style={{ textAlign: 'right', minWidth: 0 }}>
        {hist.safetyScore != null ? (
          <>
            <span
              style={{
                fontSize: 14,
                fontWeight: 700,
                color: scoreColor(hist.safetyScore),
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {hist.safetyScore}
            </span>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                minWidth: 18,
                height: 18,
                padding: '0 5px',
                marginLeft: 6,
                borderRadius: 5,
                background: `${gradeColor(hist.grade)}1a`,
                color: gradeColor(hist.grade),
                fontSize: 10,
                fontWeight: 700,
              }}
            >
              {hist.grade || '—'}
            </span>
          </>
        ) : (
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>—</span>
        )}
      </div>

      <div style={{ textAlign: 'right' }}>
        {live.score != null ? (
          <span
            style={{
              fontSize: 13,
              fontWeight: 700,
              color: scoreColor(live.score),
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {live.score}
          </span>
        ) : (
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>—</span>
        )}
      </div>

      <div style={{ minWidth: 0 }}>
        <DriverRiskBadge level={riskLevel} size="sm" />
      </div>

      <div style={{ textAlign: 'right', fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
        {hist.tripsCompleted ?? '—'}
      </div>

      <div style={{ textAlign: 'right', fontSize: 12, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
        {formatKm(hist.totalDistanceKm)}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        {trend && TrendIcon ? (
          <>
            <TrendIcon size={13} strokeWidth={2} style={{ color: trend.color, flexShrink: 0 }} />
            <span style={{ fontSize: 11, color: trend.color, fontWeight: 500 }}>
              {hist.scoreDelta != null && Math.abs(hist.scoreDelta) > 0
                ? `${hist.scoreDelta > 0 ? '+' : ''}${hist.scoreDelta}`
                : '—'}
            </span>
          </>
        ) : (
          <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
            {hist.safetyScore == null ? 'No score' : '—'}
          </span>
        )}
      </div>

      <div style={{ minWidth: 0 }}>
        <div
          style={{
            fontSize: 11,
            color: keyEvent ? 'var(--color-text-secondary)' : 'var(--color-text-muted)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {keyEvent || '—'}
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', color: 'var(--color-text-muted)' }}>
        <ChevronRight size={14} />
      </div>
    </div>
  );
}
