import { memo } from 'react';
import { AlertTriangle, ArrowRight, Radio } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useDashboard } from '../../hooks/useDashboard';
import { useVehicleDrawer } from '../../context/VehicleDrawerContext';
import { useRelativeTime } from '../../hooks/useRelativeTime';
import { TRIAGE_META } from '../../utils/dashboard';

function attentionRows(rows) {
  return (Array.isArray(rows) ? rows : []).filter((r) => r.level !== 'normal');
}

/**
 * Attention-first queue. Rows are ranked by the canonical triage ladder
 * (critical -> high -> medium -> stale). When the fleet is offline, rows
 * fall into the "No Live Data" level so attention stays honest instead of
 * pretending nothing is wrong.
 */
export const AttentionRequired = memo(function AttentionRequired() {
  const { triageRows, attention, connState } = useDashboard();
  const { openDrawer } = useVehicleDrawer();
  const rows = attentionRows(triageRows);

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
          padding: '14px 20px',
          borderBottom: '1px solid var(--color-border-light)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <AlertTriangle size={14} style={{ color: attention.total > 0 ? 'var(--color-red)' : 'var(--color-accent)' }} />
          <div>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Attention Required
            </span>
            <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 6 }}>
              {attention.total} {attention.total === 1 ? 'vehicle' : 'vehicles'}
            </span>
          </div>
        </div>
        <Link
          to="/alerts"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            fontSize: 12,
            color: 'var(--color-accent)',
            fontWeight: 500,
            textDecoration: 'none',
            whiteSpace: 'nowrap',
            transition: 'opacity 0.15s ease',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.7'; }}
          onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
        >
          View alerts <ArrowRight size={13} />
        </Link>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {rows.length === 0 ? (
          <div style={{ padding: '22px 20px', textAlign: 'center', fontSize: 12, color: 'var(--color-text-muted)' }}>
            {connState === 'live'
              ? 'No vehicles require attention right now.'
              : 'No vehicles flagged for attention. Live data is unavailable.'}
          </div>
        ) : (
          rows.map((row, i) => (
            <AttentionRow
              key={row.id}
              row={row}
              last={i === rows.length - 1}
              onOpen={() => openDrawer({ id: row.id })}
            />
          ))
        )}
      </div>
    </div>
  );
});

function AttentionRow({ row, last, onOpen }) {
  const timeAgo = useRelativeTime(row.lastUpdate);
  const meta = TRIAGE_META[row.level] || TRIAGE_META.normal;

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
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '11px 20px',
        borderBottom: last ? 'none' : '1px solid var(--color-border-light)',
        cursor: 'pointer',
        transition: 'background-color 0.12s ease',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 4,
          padding: '2px 7px',
          borderRadius: 5,
          background: meta.bg,
          color: meta.color,
          fontSize: 10,
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
          whiteSpace: 'nowrap',
          flexShrink: 0,
        }}
      >
        {row.level === 'critical' && <Radio size={10} />}
        {meta.label}
      </span>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {row.name}
          </span>
          {row.driver && row.driver !== '—' && (
            <span style={{ fontSize: 11, color: 'var(--color-text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              · {row.driver}
            </span>
          )}
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginTop: 1 }}>
          {row.reasons.length > 0 ? row.reasons.join(' · ') : 'No flagged issues.'}
        </div>
      </div>

      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
          {row.healthScore == null ? '\u2014' : row.healthScore}
        </div>
        <div style={{ fontSize: 10, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums', marginTop: 2 }}>
          {row.lastUpdate ? timeAgo : '—'}
        </div>
      </div>
    </div>
  );
}
