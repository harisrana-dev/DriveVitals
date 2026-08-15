import { memo } from 'react';
import { AlertTriangle, ArrowUpRight } from 'lucide-react';
import { SeverityBadge } from './SeverityBadge';
import { AlertStatusBadge } from './AlertStatusBadge';
import { useRelativeTime } from '../../hooks/useRelativeTime';
import { alertStaleness, formatEventCounts } from '../../utils/alerts';

const STALE_LABEL = {
  stale: 'Stale',
  'hard-stale': 'Hard Stale',
};

/**
 * Attention-required queue: active, critical-or-high incidents that are
 * still unacknowledged. Incidents that are old enough to be stale are
 * shown muted — they remain visible but are no longer treated as live.
 */
export const CriticalIncidentQueue = memo(function CriticalIncidentQueue({ incidents, onIncidentClick, selectedKey }) {
  const queue = (Array.isArray(incidents) ? incidents : []).filter(
    (i) => i.status === 'active' && (i.severity === 'critical' || i.severity === 'high') && !i.acknowledged
  );

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
        <AlertTriangle size={14} style={{ color: 'var(--color-red)' }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
          Critical Incident Queue
        </span>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 4 }}>
          {queue.length} open
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 360, overflowY: 'auto' }}>
        {queue.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '8px 0' }}>
            No critical or high-severity active incidents awaiting acknowledgement.
          </div>
        ) : (
          queue.map((incident) => (
            <QueueRow
              key={incident.key}
              incident={incident}
              selected={incident.key === selectedKey}
              onClick={() => onIncidentClick && onIncidentClick(incident)}
            />
          ))
        )}
      </div>
    </div>
  );
});

function QueueRow({ incident, selected, onClick }) {
  const timeAgo = useRelativeTime(incident.created_at);
  const staleness = alertStaleness(incident);
  const stale = staleness.level === 'stale' || staleness.level === 'hard-stale';
  const color = incident.severity === 'critical' ? 'var(--color-red)' : 'var(--color-amber)';
  const bg = incident.severity === 'critical' ? 'var(--color-red-bg)' : 'var(--color-amber-bg)';
  const eventSummary = formatEventCounts(incident.eventCounts);

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && onClick) {
          e.preventDefault();
          onClick();
        }
      }}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '9px 12px',
        borderRadius: 8,
        background: selected ? 'var(--color-accent-subtle)' : stale ? 'var(--color-surface-hover)' : bg,
        border: selected ? '1px solid var(--color-accent)' : stale ? '1px dashed var(--color-border)' : `1px solid ${color}`,
        cursor: 'pointer',
        opacity: stale ? 0.7 : 1,
        transition: 'all 0.15s ease',
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
          <span
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {incident.vehicle_name || incident.vehicle_id}
          </span>
          <SeverityBadge severity={incident.severity} size="sm" />
        </div>
        <div
          style={{
            fontSize: 11,
            color: 'var(--color-text-secondary)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {incident.driver_name ? `${incident.driver_name} · ` : ''}{incident.title}
          {incident.groupCount > 1 ? ` · ${incident.groupCount} signals` : ''}
        </div>
        {eventSummary && (
          <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginTop: 2 }}>
            {eventSummary}
          </div>
        )}
      </div>

      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, justifyContent: 'flex-end' }}>
          <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
            {incident.created_at ? timeAgo : '—'}
          </span>
          {stale && (
            <span
              style={{
                fontSize: 9,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                color: 'var(--color-text-muted)',
              }}
            >
              {STALE_LABEL[staleness.level]}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, justifyContent: 'flex-end', marginTop: 3 }}>
          <AlertStatusBadge status="active" size="sm" />
          <button
            onClick={(e) => { e.stopPropagation(); if (onClick) onClick(); }}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 3,
              padding: '3px 8px',
              borderRadius: 6,
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              color: 'var(--color-text-secondary)',
              fontSize: 10,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: 'inherit',
              lineHeight: 1,
              transition: 'all 0.12s ease',
            }}
          >
            Open
            <ArrowUpRight size={11} />
          </button>
        </div>
      </div>
    </div>
  );
}
