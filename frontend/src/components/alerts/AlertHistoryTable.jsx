import { memo, useRef, useEffect } from 'react';
import { ArrowUpRight, Check, ChevronsUpDown } from 'lucide-react';
import { useLiveData } from '../../context/LiveDataContext';
import { severityRank } from '../../services/alertAdapter';
import { SeverityBadge } from './SeverityBadge';
import { AlertStatusBadge } from './AlertStatusBadge';
import { AlertCard } from './AlertCard';
import { alertAge, alertStaleness, formatEventCounts, categoryDisplayLabel } from '../../utils/alerts';

const GRID = '76px 1.15fr 0.95fr 1.6fr 0.95fr 0.8fr 1fr 1.2fr 96px';

const SORT_OPTIONS = [
  { key: 'severity', label: 'Severity' },
  { key: 'newest', label: 'Newest' },
  { key: 'oldest', label: 'Oldest' },
  { key: 'vehicle', label: 'Vehicle' },
];

function incidentTime(incident) {
  return incident.created_at ? new Date(incident.created_at).getTime() || 0 : 0;
}

function sortIncidents(incidents, sortBy) {
  const list = [...incidents];
  switch (sortBy) {
    case 'newest':
      return list.sort((a, b) => incidentTime(b) - incidentTime(a));
    case 'oldest':
      return list.sort((a, b) => incidentTime(a) - incidentTime(b));
    case 'vehicle':
      return list.sort(
        (a, b) =>
          a.vehicle_id.localeCompare(b.vehicle_id) || incidentTime(b) - incidentTime(a)
      );
    case 'severity':
    default:
      return list.sort(
        (a, b) =>
          severityRank(a.severity) - severityRank(b.severity) ||
          incidentTime(b) - incidentTime(a)
      );
  }
}

function formatCellTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  const age = Date.now() - d.getTime();
  if (age < 24 * 60 * 60 * 1000) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  return `${d.toLocaleDateString([], { month: 'short', day: 'numeric' })} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
}

export const AlertHistoryTable = memo(function AlertHistoryTable({
  incidents,
  onIncidentClick,
  selectedKey,
  sortBy,
  onSortChange,
  onAcknowledgeAllPassive,
  showAcknowledgeAllPassive,
}) {
  const list = sortIncidents(incidents, sortBy);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [incidents]);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 8, marginBottom: 8 }}>
        {showAcknowledgeAllPassive && onAcknowledgeAllPassive && (
          <button
            onClick={onAcknowledgeAllPassive}
            style={{
              padding: '4px 10px',
              borderRadius: 6,
              border: '1px solid var(--color-border)',
              background: 'transparent',
              color: 'var(--color-text-secondary)',
              fontSize: 11,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: 'inherit',
              transition: 'all 0.12s ease',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-accent-subtle)'; e.currentTarget.style.color = 'var(--color-accent)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--color-text-secondary)'; }}
          >
            Acknowledge All Passive
          </button>
        )}
        <ChevronsUpDown size={12} style={{ color: 'var(--color-text-muted)' }} />
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Sort</span>
        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value)}
          style={{
            padding: '3px 8px',
            borderRadius: 6,
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-primary)',
            fontSize: 11,
            fontFamily: 'inherit',
            cursor: 'pointer',
          }}
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.key} value={o.key}>{o.label}</option>
          ))}
        </select>
      </div>

      <div className="alerts-history-desktop">
        <div style={{ border: '1px solid var(--color-border)', borderRadius: 10, overflow: 'hidden' }}>
          <div ref={scrollRef} style={{ maxHeight: 460, overflowY: 'auto', scrollbarGutter: 'stable' }}>
            <div
              style={{
                position: 'sticky',
                top: 0,
                zIndex: 2,
                display: 'grid',
                gridTemplateColumns: GRID,
                gap: 10,
                padding: '10px 12px 8px',
                fontSize: 10,
                fontWeight: 600,
                color: 'var(--color-text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                background: 'var(--color-surface)',
                borderBottom: '1px solid var(--color-border)',
              }}
            >
              <span>Time</span>
              <span>Vehicle</span>
              <span>Driver</span>
              <span>Incident</span>
              <span>Category</span>
              <span>Severity</span>
              <span>Status</span>
              <span>Evidence</span>
              <span style={{ textAlign: 'right' }}>Action</span>
            </div>

            {list.length === 0 ? (
              <div style={{ padding: '28px 16px', textAlign: 'center', fontSize: 12, color: 'var(--color-text-muted)' }}>
                No alerts match the current filters.
              </div>
            ) : (
              list.map((incident) => (
                <HistoryRow
                  key={incident.key}
                  incident={incident}
                  selected={incident.key === selectedKey}
                  onClick={() => onIncidentClick && onIncidentClick(incident)}
                />
              ))
            )}
          </div>
        </div>
      </div>

      <div className="alerts-history-mobile" style={{ display: 'none', flexDirection: 'column', gap: 10 }}>
        {list.length === 0 ? (
          <div style={{ padding: '28px 16px', textAlign: 'center', fontSize: 12, color: 'var(--color-text-muted)' }}>
            No alerts match the current filters.
          </div>
        ) : (
          list.map((incident) => (
            <AlertCard
              key={incident.key}
              alert={incident}
              stale={alertStaleness(incident).level === 'stale' || alertStaleness(incident).level === 'hard-stale'}
              onClick={() => onIncidentClick && onIncidentClick(incident)}
            />
          ))
        )}
      </div>

      <style>{`
        @media (max-width: 960px) {
          .alerts-history-desktop { display: none; }
          .alerts-history-mobile { display: flex !important; }
        }
      `}</style>
    </div>
  );
});

function HistoryRow({ incident, selected, onClick }) {
  const { acknowledgeAlert } = useLiveData();
  const timeAgo = alertAge(incident.created_at);
  const staleness = alertStaleness(incident);
  const stale = staleness.level === 'stale' || staleness.level === 'hard-stale';
  const resolved = incident.status === 'resolved';
  const isPassive = resolved && !incident.acknowledged;
  const eventSummary = formatEventCounts(incident.eventCounts);
  const category = categoryDisplayLabel(incident.category);

  const handleQuickAck = (e) => {
    e.stopPropagation();
    if (incident.children.length === 1) {
      acknowledgeAlert(incident.children[0].alert_id);
    }
  };

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
        display: 'grid',
        gridTemplateColumns: GRID,
        gap: 10,
        alignItems: 'center',
        padding: '9px 12px',
        borderBottom: '1px solid var(--color-border-light)',
        background: selected ? 'var(--color-accent-subtle)' : 'transparent',
        borderLeft: isPassive ? '3px solid var(--color-text-muted)' : '3px solid transparent',
        cursor: 'pointer',
        opacity: resolved || (stale && !selected) ? 0.55 : stale ? 0.8 : 1,
        transition: 'background-color 0.12s ease',
      }}
      onMouseEnter={(e) => { if (!selected) e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
      onMouseLeave={(e) => { if (!selected) e.currentTarget.style.background = 'transparent'; }}
    >
      <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
        {formatCellTime(incident.created_at)}
      </span>

      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {incident.vehicle_name || incident.vehicle_id}
      </span>

      <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {incident.driver_name || '—'}
      </span>

      <span style={{ minWidth: 0 }}>
        <span
          style={{
            display: 'block',
            fontSize: 12,
            fontWeight: 500,
            color: 'var(--color-text-primary)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {incident.title}
        </span>
        <span style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>
          {incident.created_at ? timeAgo : '—'}
          {incident.groupCount > 1 ? ` · ${incident.groupCount} signals` : ''}
        </span>
      </span>

      <span style={{ fontSize: 11, color: category === 'Unclassified' ? 'var(--color-text-muted)' : 'var(--color-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {category}
      </span>

      <span><SeverityBadge severity={incident.severity} size="sm" /></span>

      <span style={{ display: 'flex', alignItems: 'center', gap: 5, minWidth: 0 }}>
        <AlertStatusBadge status={incident.status} size="sm" />
        {isPassive && (
          <span
            style={{
              fontSize: 9,
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              color: 'var(--color-text-muted)',
              background: 'var(--color-surface-hover)',
              padding: '1px 5px',
              borderRadius: 3,
              whiteSpace: 'nowrap',
            }}
          >
            Passive
          </span>
        )}
        {stale && !resolved && (
          <span
            style={{
              fontSize: 9,
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              color: 'var(--color-text-muted)',
              whiteSpace: 'nowrap',
            }}
          >
            {staleness.level === 'hard-stale' ? 'Hard Stale' : 'Stale'}
          </span>
        )}
      </span>

      <span style={{ fontSize: 10, color: 'var(--color-text-muted)', minWidth: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {eventSummary || incident.message || '—'}
      </span>

      <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4 }}>
        {incident.status === 'active' && !incident.acknowledged && incident.children.length === 1 && (
          <button
            onClick={handleQuickAck}
            title="Acknowledge"
            aria-label="Acknowledge"
            style={{
              width: 26,
              height: 26,
              borderRadius: 6,
              border: '1px solid var(--color-border)',
              background: 'transparent',
              color: 'var(--color-accent)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.12s ease',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-accent-subtle)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
          >
            <Check size={13} />
          </button>
        )}
        <button
          onClick={(e) => { e.stopPropagation(); if (onClick) onClick(); }}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 3,
            padding: '4px 8px',
            borderRadius: 6,
            border: '1px solid var(--color-border)',
            background: 'transparent',
            color: 'var(--color-text-secondary)',
            fontSize: 10,
            fontWeight: 600,
            cursor: 'pointer',
            fontFamily: 'inherit',
            lineHeight: 1,
            transition: 'all 0.12s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-surface-hover)';
            e.currentTarget.style.color = 'var(--color-text-primary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = 'var(--color-text-secondary)';
          }}
        >
          Open
          <ArrowUpRight size={11} />
        </button>
      </span>
    </div>
  );
}
