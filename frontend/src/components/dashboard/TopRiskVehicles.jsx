import { memo } from 'react';
import { Gauge } from 'lucide-react';
import { useDashboard } from '../../hooks/useDashboard';
import { useVehicleDrawer } from '../../context/useVehicleDrawer';
import { TRIAGE_META } from '../../utils/dashboard';

const GRID = '1.4fr 1fr 52px 46px 64px 1.4fr';

function riskRows(rows) {
  return (Array.isArray(rows) ? rows : []).filter(
    (r) => r.level === 'critical' || r.level === 'high' || r.level === 'medium'
  );
}

/**
 * Top risk vehicles by canonical triage level and severity-weighted alert
 * risk. Risk is the canonical `computeVehicleRisk` score from active
 * alerts — no invented risk formula. Rows open the vehicle drawer.
 */
export const TopRiskVehicles = memo(function TopRiskVehicles() {
  const { triageRows } = useDashboard();
  const { openDrawer } = useVehicleDrawer();
  const rows = riskRows(triageRows);
  const maxRisk = Math.max(...rows.map((r) => r.riskScore), 1);

  return (
    <div
      className="fade-in"
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
        minWidth: 0,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
        <Gauge size={14} style={{ color: 'var(--color-amber)' }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
          Top Risk Vehicles
        </span>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 4 }}>
          {rows.length} flagged
        </span>
      </div>
      <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 10 }}>
        Ranked by triage level and severity-weighted active alerts (critical 5 \u00B7 high 4 \u00B7 medium 2)
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: GRID,
          gap: 8,
          padding: '0 4px 6px',
          fontSize: 10,
          fontWeight: 600,
          color: 'var(--color-text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        <span>Vehicle</span>
        <span>Driver</span>
        <span style={{ textAlign: 'right' }}>Alerts</span>
        <span style={{ textAlign: 'right' }}>Live</span>
        <span style={{ textAlign: 'right' }}>Risk</span>
        <span>Reason</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {rows.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '8px 4px' }}>
            No vehicles are currently flagged for attention.
          </div>
        ) : (
          rows.slice(0, 6).map((row) => (
            <RiskRow
              key={row.id}
              row={row}
              maxRisk={maxRisk}
              onOpen={() => openDrawer({ id: row.id })}
            />
          ))
        )}
      </div>
    </div>
  );
});

function RiskRow({ row, maxRisk, onOpen }) {
  const meta = TRIAGE_META[row.level] || TRIAGE_META.normal;
  const barWidth = Math.max(6, (row.riskScore / maxRisk) * 100);

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`Open ${row.name}`}
      className="row-focusable"
      onClick={onOpen}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && onOpen) {
          e.preventDefault();
          onOpen();
        }
      }}
      style={{
        display: 'grid',
        gridTemplateColumns: GRID,
        gap: 8,
        alignItems: 'center',
        padding: '7px 4px',
        borderRadius: 8,
        cursor: 'pointer',
        transition: 'background-color 0.12s ease',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      <span style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
        <span
          style={{
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: meta.color,
            flexShrink: 0,
          }}
        />
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {row.name}
        </span>
      </span>
      <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {row.driver || '—'}
      </span>
      <span style={{ fontSize: 11, fontWeight: 600, textAlign: 'right', color: row.activeAlertCount > 0 ? 'var(--color-red)' : 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
        {row.activeAlertCount}
      </span>
      <span style={{ fontSize: 11, textAlign: 'right', color: row.liveEventCount > 0 ? 'var(--color-red)' : 'var(--color-text-muted)', fontWeight: row.liveEventCount > 0 ? 600 : 400, fontVariantNumeric: 'tabular-nums' }}>
        {row.liveEventCount}
      </span>
      <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4 }}>
        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
          {row.riskScore}
        </span>
        <span style={{ width: 22, height: 3, borderRadius: 2, background: 'var(--color-border-light)', overflow: 'hidden' }}>
          <span
            style={{
              display: 'block',
              height: '100%',
              width: `${barWidth}%`,
              background: row.riskScore >= 9 ? 'var(--color-red)' : row.riskScore >= 5 ? 'var(--color-amber)' : 'var(--color-accent)',
            }}
          />
        </span>
      </span>
      <span style={{ fontSize: 10, color: 'var(--color-text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {row.reasons[0] || '\u2014'}
      </span>
    </div>
  );
}
