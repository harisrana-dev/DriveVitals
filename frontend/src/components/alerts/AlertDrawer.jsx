import { X, Check, CheckCircle2, ExternalLink, Wrench } from 'lucide-react';
import { useLiveData } from '../../context/LiveDataContext';
import { SeverityBadge } from './SeverityBadge';
import { AlertStatusBadge } from './AlertStatusBadge';
import { useRelativeTime } from '../../hooks/useRelativeTime';
import {
  severityColor,
  alertStaleness,
  EVENT_COUNT_ORDER,
} from '../../utils/alerts';

const EVENT_COUNT_LABELS = {
  total: 'events',
  overspeeding: 'overspeed',
  harsh_braking: 'braking',
  harsh_acceleration: 'acceleration',
  severe: 'severe',
};

function formatDateTime(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleString();
}

function titleCase(value) {
  if (!value) return null;
  return String(value).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Incident command panel. Receives a grouped incident (not a raw alert)
 * so trip fan-out signals are presented together. Actions apply per alert
 * in the Related Alerts list; every change flows back through the shared
 * LiveData context so the panel re-derives live. No nested drawers: each
 * drill-down callback is one context surface.
 */
export function AlertDrawer({
  incident,
  onClose,
  onViewVehicle,
  onViewDriver,
  onViewTrip,
  onViewMaintenance,
}) {
  if (!incident) return null;

  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.3)',
          zIndex: 300,
          animation: 'fadeIn 0.15s ease-out',
        }}
      />
      <div
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          width: 480,
          maxWidth: '90vw',
          height: '100vh',
          background: 'var(--color-surface)',
          borderLeft: '1px solid var(--color-border)',
          boxShadow: 'var(--color-shadow-lg)',
          zIndex: 301,
          display: 'flex',
          flexDirection: 'column',
          animation: 'slideInRight 0.2s ease-out',
        }}
      >
        <DrawerContent
          incident={incident}
          onClose={onClose}
          onViewVehicle={onViewVehicle}
          onViewDriver={onViewDriver}
          onViewTrip={onViewTrip}
          onViewMaintenance={onViewMaintenance}
        />
      </div>
    </>
  );
}

function DrawerContent({ incident, onClose, onViewVehicle, onViewDriver, onViewTrip, onViewMaintenance }) {
  return (
    <>
      <Header incident={incident} onClose={onClose} />
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 20,
          display: 'flex',
          flexDirection: 'column',
          gap: 20,
        }}
      >
        <IncidentInfo incident={incident} />
        <Message incident={incident} />
        <Evidence incident={incident} />
        <RelatedAlerts incident={incident} />
        <DrillDownActions
          incident={incident}
          onViewVehicle={onViewVehicle}
          onViewDriver={onViewDriver}
          onViewTrip={onViewTrip}
          onViewMaintenance={onViewMaintenance}
        />
      </div>
      <Footer incident={incident} onClose={onClose} />
    </>
  );
}

function Header({ incident, onClose }) {
  const color = severityColor(incident.severity);
  const staleness = alertStaleness(incident);
  const stale = staleness.level === 'stale' || staleness.level === 'hard-stale';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '16px 20px',
        borderBottom: '1px solid var(--color-border)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            background: color + '18',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color,
            fontSize: 16,
            fontWeight: 600,
            flexShrink: 0,
          }}
        >
          {incident.vehicle_name?.charAt(0)?.toUpperCase() || '?'}
        </div>
        <div style={{ minWidth: 0 }}>
          <div
            style={{
              fontSize: 16,
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {incident.title}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
            <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
              {incident.alert_ids.length > 1 ? `${incident.alert_ids.length} alerts` : incident.alert_ids[0]}
            </span>
            <SeverityBadge severity={incident.severity} size="sm" />
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
                {staleness.level === 'hard-stale' ? 'Hard Stale' : 'Stale'}
              </span>
            )}
          </div>
        </div>
      </div>
      <button
        onClick={onClose}
        aria-label="Close"
        style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-text-muted)',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          transition: 'all 0.15s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'var(--color-surface-hover)';
          e.currentTarget.style.color = 'var(--color-text-primary)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'transparent';
          e.currentTarget.style.color = 'var(--color-text-muted)';
        }}
      >
        <X size={18} />
      </button>
    </div>
  );
}

function IncidentInfo({ incident }) {
  const created = formatDateTime(incident.created_at);
  const resolvedAt = formatDateTime(incident.resolved_at);
  const acknowledgedAt = incident.acknowledged
    ? formatDateTime(incident.children.find((c) => c.acknowledged_at)?.acknowledged_at)
    : null;

  return (
    <Section title="Incident Details">
      <div
        style={{
          padding: '14px 16px',
          borderRadius: 8,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          fontSize: 12,
        }}
      >
        <InfoRow label="Vehicle" value={incident.vehicle_name || incident.vehicle_id || '—'} />
        <InfoRow label="Driver" value={incident.driver_name || incident.driver_id || '—'} />
        <InfoRow label="Trip" value={incident.trip_id || '—'} />
        <InfoRow label="Category" value={incident.category_label} />
        <InfoRow label="Condition" value={incident.condition ? titleCase(incident.condition) : '—'} />
        <InfoRow label="Source" value={titleCase(incident.alert_type) || '—'} />
        {incident.groupCount > 1 && (
          <InfoRow label="Signals" value={`${incident.groupCount} alerts in one trip`} />
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ color: 'var(--color-text-muted)', minWidth: 80 }}>Severity</span>
          <SeverityBadge severity={incident.severity} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ color: 'var(--color-text-muted)', minWidth: 80 }}>Status</span>
          <AlertStatusBadge status={incident.status} />
        </div>
        <InfoRow label="Created" value={created || '—'} />
        <InfoRow label="Acknowledged" value={acknowledgedAt || '—'} />
        <InfoRow label="Resolved" value={resolvedAt || '—'} />
      </div>
    </Section>
  );
}

function InfoRow({ label, value }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span style={{ color: 'var(--color-text-muted)', minWidth: 80 }}>{label}</span>
      <span style={{ color: 'var(--color-text-primary)', fontWeight: 500, wordBreak: 'break-word' }}>{value}</span>
    </div>
  );
}

function Message({ incident }) {
  return (
    <Section title="Message">
      <div
        style={{
          padding: '14px 16px',
          borderRadius: 8,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
          fontSize: 12,
          lineHeight: 1.5,
          color: 'var(--color-text-primary)',
        }}
      >
        {incident.message || 'No message recorded.'}
      </div>
    </Section>
  );
}

function Evidence({ incident }) {
  const counts = incident.eventCounts || {};
  const countChips = EVENT_COUNT_ORDER.filter((k) => counts[k] > 0);

  const representative = incident.children[0];
  const evidence = representative?.evidence && typeof representative.evidence === 'object'
    ? Object.entries(representative.evidence).filter(([k, v]) => k !== 'event_counts' && v != null && v !== '')
    : [];

  const hasCounts = countChips.length > 0;

  if (!hasCounts && evidence.length === 0) {
    return (
      <Section title="Evidence">
        <div
          style={{
            padding: '12px 14px',
            borderRadius: 8,
            background: 'var(--color-bg)',
            border: '1px solid var(--color-border-light)',
            fontSize: 12,
            color: 'var(--color-text-muted)',
          }}
        >
          No evidence recorded.
        </div>
      </Section>
    );
  }

  return (
    <Section title="Evidence">
      <div
        style={{
          padding: '14px 16px',
          borderRadius: 8,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
          fontSize: 12,
        }}
      >
        {hasCounts && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {countChips.map((k) => (
              <span
                key={k}
                style={{
                  padding: '3px 9px',
                  borderRadius: 8,
                  background: 'var(--color-surface-hover)',
                  border: '1px solid var(--color-border-light)',
                  fontSize: 11,
                  fontWeight: 600,
                  color: 'var(--color-text-primary)',
                  fontVariantNumeric: 'tabular-nums',
                  lineHeight: 1,
                }}
              >
                {counts[k]} {EVENT_COUNT_LABELS[k] || k.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        )}
        {evidence.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {evidence.map(([key, value]) => (
              <div key={key} style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                <span style={{ color: 'var(--color-text-muted)', textTransform: 'capitalize' }}>
                  {titleCase(key)}
                </span>
                <span
                  style={{
                    color: 'var(--color-text-primary)',
                    fontWeight: 500,
                    fontVariantNumeric: 'tabular-nums',
                    textAlign: 'right',
                    wordBreak: 'break-word',
                  }}
                >
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </Section>
  );
}

function RelatedAlerts({ incident }) {
  return (
    <Section title="Related Alerts">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {incident.children.map((child) => (
          <ChildAlertRow key={child.alert_id} child={child} />
        ))}
      </div>
    </Section>
  );
}

function ChildAlertRow({ child }) {
  const { acknowledgeAlert, resolveAlert } = useLiveData();
  const timeAgo = useRelativeTime(child.created_at);
  const isActive = child.status === 'active';

  return (
    <div
      style={{
        padding: '10px 12px',
        borderRadius: 8,
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border-light)',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
          <SeverityBadge severity={child.severity} size="sm" />
          <AlertStatusBadge status={child.status} size="sm" />
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {titleCase(child.condition) || child.title}
          </span>
        </div>
        <div style={{ fontSize: 10, color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
          {child.alert_id}
          {child.created_at ? ` · ${timeAgo}` : ''}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 4, flexShrink: 0 }}>
        {isActive && !child.acknowledged && (
          <ActionBtn
            label="Acknowledge"
            icon={<Check size={12} />}
            onClick={() => acknowledgeAlert(child.alert_id)}
            primary
          />
        )}
        {isActive && (
          <ActionBtn
            label="Resolve"
            icon={<CheckCircle2 size={12} />}
            onClick={() => resolveAlert(child.alert_id)}
          />
        )}
      </div>
    </div>
  );
}

function ActionBtn({ label, icon, onClick, primary }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '4px 9px',
        borderRadius: 6,
        border: primary ? 'none' : '1px solid var(--color-border)',
        background: primary ? 'var(--color-accent)' : 'transparent',
        color: primary ? '#fff' : 'var(--color-text-secondary)',
        fontSize: 10,
        fontWeight: 600,
        cursor: 'pointer',
        fontFamily: 'inherit',
        lineHeight: 1,
        transition: 'all 0.12s ease',
      }}
      onMouseEnter={(e) => {
        if (primary) e.currentTarget.style.opacity = '0.85';
        else {
          e.currentTarget.style.background = 'var(--color-surface-hover)';
          e.currentTarget.style.color = 'var(--color-text-primary)';
        }
      }}
      onMouseLeave={(e) => {
        if (primary) e.currentTarget.style.opacity = '1';
        else {
          e.currentTarget.style.background = 'transparent';
          e.currentTarget.style.color = 'var(--color-text-secondary)';
        }
      }}
    >
      {icon}
      {label}
    </button>
  );
}

function DrillDownActions({ incident, onViewVehicle, onViewDriver, onViewTrip, onViewMaintenance }) {
  const links = [];
  if (incident.vehicle_id && onViewVehicle) {
    links.push({ label: 'View Vehicle', icon: <ExternalLink size={12} />, onClick: () => onViewVehicle(incident.vehicle_id) });
  }
  if (incident.driver_id && onViewDriver) {
    links.push({ label: 'View Driver', icon: <ExternalLink size={12} />, onClick: () => onViewDriver(incident.driver_id) });
  }
  if (incident.trip_id && onViewTrip) {
    links.push({ label: 'View Trip', icon: <ExternalLink size={12} />, onClick: () => onViewTrip(incident.trip_id) });
  }
  if (incident.category === 'maintenance' && onViewMaintenance) {
    links.push({ label: 'View Maintenance', icon: <Wrench size={12} />, onClick: () => onViewMaintenance(incident.vehicle_id) });
  }

  if (links.length === 0) return null;

  return (
    <Section title="Actions">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {links.map((link) => (
          <button
            key={link.label}
            onClick={link.onClick}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '8px 12px',
              borderRadius: 8,
              border: '1px solid var(--color-border)',
              background: 'transparent',
              color: 'var(--color-text-secondary)',
              fontSize: 12,
              fontWeight: 500,
              cursor: 'pointer',
              fontFamily: 'inherit',
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
            {link.icon}
            {link.label}
          </button>
        ))}
      </div>
    </Section>
  );
}

function Section({ title, children }) {
  return (
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
        {title}
      </div>
      {children}
    </div>
  );
}

function Footer({ incident, onClose }) {
  const { acknowledgeAlert, resolveAlert } = useLiveData();
  const single = incident.children.length === 1 ? incident.children[0] : null;
  const isActive = single ? single.status === 'active' : false;

  return (
    <div
      style={{
        padding: '12px 20px',
        borderTop: '1px solid var(--color-border)',
        display: 'flex',
        gap: 8,
      }}
    >
      {single && isActive && !single.acknowledged && (
        <button
          onClick={() => acknowledgeAlert(single.alert_id)}
          style={footerBtnPrimary}
          onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.85'; }}
          onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
        >
          <Check size={14} />
          Acknowledge
        </button>
      )}
      {single && isActive && (
        <button
          onClick={() => resolveAlert(single.alert_id)}
          style={footerBtnGhost}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-surface-hover)';
            e.currentTarget.style.color = 'var(--color-text-primary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = 'var(--color-text-secondary)';
          }}
        >
          <CheckCircle2 size={14} />
          Resolve
        </button>
      )}
      {!single && (
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', padding: '8px 4px', flex: 1 }}>
          This incident groups {incident.groupCount} alerts — acknowledge or resolve each in Related Alerts.
        </span>
      )}
      <button
        onClick={onClose}
        style={footerBtnGhost}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'var(--color-surface-hover)';
          e.currentTarget.style.color = 'var(--color-text-primary)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'transparent';
          e.currentTarget.style.color = 'var(--color-text-secondary)';
        }}
      >
        Close
      </button>
    </div>
  );
}

const footerBtnBase = {
  flex: 1,
  padding: '8px 12px',
  borderRadius: 8,
  fontSize: 13,
  fontWeight: 500,
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 6,
  fontFamily: 'inherit',
  transition: 'all 0.15s ease',
};

const footerBtnPrimary = {
  ...footerBtnBase,
  border: 'none',
  background: 'var(--color-accent)',
  color: '#fff',
};

const footerBtnGhost = {
  ...footerBtnBase,
  border: '1px solid var(--color-border)',
  background: 'transparent',
  color: 'var(--color-text-secondary)',
};
