import { X } from 'lucide-react';
import { useAlert } from '../../hooks/useAlerts';
import { SeverityBadge } from './SeverityBadge';
import { AlertStatusBadge } from './AlertStatusBadge';
import { severityColor } from '../../utils/alerts';
import { getSuggestedAction, buildIncidentTimeline } from '../../utils/alerts';

export function AlertDrawer({ alertId, onClose }) {
  const alert = useAlert(alertId);
  if (!alert) return null;

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
        <DrawerContent alert={alert} onClose={onClose} />
      </div>
    </>
  );
}

function DrawerContent({ alert, onClose }) {
  const timeline = buildIncidentTimeline(alert);
  const action = getSuggestedAction(alert);

  return (
    <>
      <Header alert={alert} onClose={onClose} />
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
        <IncidentInfo alert={alert} />
        <LiveTelemetry alert={alert} />
        <IncidentTimeline timeline={timeline} />
        <SuggestedAction action={action} />
      </div>
      <Footer onClose={onClose} />
    </>
  );
}

function Header({ alert, onClose }) {
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
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            background: severityColor(alert.severity) + '18',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: severityColor(alert.severity),
            fontSize: 16,
            fontWeight: 600,
            flexShrink: 0,
          }}
        >
          {alert.vehicle_name?.charAt(0)?.toUpperCase() || '?'}
        </div>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            {alert.eventType}
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
            {alert.alert_id || alert.id}
          </div>
        </div>
      </div>
      <button
        onClick={onClose}
        aria-label="Close"
        style={{
          width: 32, height: 32, borderRadius: 8,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--color-text-muted)', background: 'transparent',
          border: 'none', cursor: 'pointer',
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

function IncidentInfo({ alert }) {
  return (
    <Section title="Incident Information">
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
        <InfoRow label="Vehicle" value={alert.vehicle_name} />
        <InfoRow label="Driver" value={alert.driver_name} />
        <InfoRow label="Trip" value={`${alert.vehicle_id} · Active`} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ color: 'var(--color-text-muted)', minWidth: 80 }}>Severity</span>
          <SeverityBadge severity={alert.severity} />
        </div>
        <InfoRow label="Started" value={new Date(alert.started_at).toLocaleString()} />
        <InfoRow label="Duration" value={`${Math.round((Date.now() - new Date(alert.started_at).getTime()) / 60000)} min`} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ color: 'var(--color-text-muted)', minWidth: 80 }}>Status</span>
          <AlertStatusBadge status={alert.status} />
        </div>
      </div>
    </Section>
  );
}

function InfoRow({ label, value }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span style={{ color: 'var(--color-text-muted)', minWidth: 80 }}>{label}</span>
      <span style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>{value}</span>
    </div>
  );
}

function LiveTelemetry({ alert }) {
  return (
    <Section title="Live Telemetry">
      <div
        style={{
          padding: '14px 16px',
          borderRadius: 8,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '8px 16px',
          fontSize: 12,
        }}
      >
        <TelemetryRow label="Speed" value={`${alert.speed.toFixed(1)} km/h`} />
        <TelemetryRow label="RPM" value={`${Math.round(alert.rpm)}`} />
        <TelemetryRow label="Throttle" value={`${alert.throttle_position_percent.toFixed(0)}%`} />
        <TelemetryRow label="Brake Pressure" value={`${alert.brake_pressure.toFixed(2)}`} />
        <TelemetryRow label="Engine Load" value={`${alert.engine_load_percent.toFixed(0)}%`} />
        <TelemetryRow label="Fuel Level" value={`${alert.fuel_level_percent.toFixed(0)}%`} />
        <TelemetryRow label="Coolant" value={`${alert.coolant_temperature_c.toFixed(1)} °C`} />
        <TelemetryRow label="Health" value={`${Math.round(alert.overall_health_score)}%`} />
      </div>
    </Section>
  );
}

function TelemetryRow({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <span style={{ color: 'var(--color-text-muted)' }}>{label}</span>
      <span style={{ color: 'var(--color-text-primary)', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>{value}</span>
    </div>
  );
}

function IncidentTimeline({ timeline }) {
  return (
    <Section title="Incident Timeline">
      <div
        style={{
          padding: '14px 16px',
          borderRadius: 8,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
          display: 'flex',
          flexDirection: 'column',
          gap: 0,
        }}
      >
        {timeline.map((t, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              gap: 10,
              padding: '6px 0',
              borderBottom: i < timeline.length - 1 ? '1px solid var(--color-border-light)' : 'none',
            }}
          >
            <div
              style={{
                width: 2,
                borderRadius: 1,
                background: 'var(--color-accent)',
                flexShrink: 0,
              }}
            />
            <div
              style={{
                fontSize: 11,
                color: 'var(--color-text-muted)',
                fontVariantNumeric: 'tabular-nums',
                minWidth: 50,
                flexShrink: 0,
              }}
            >
              {new Date(t.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
            <span style={{ fontSize: 12, color: 'var(--color-text-primary)' }}>{t.event}</span>
          </div>
        ))}
      </div>
    </Section>
  );
}

function SuggestedAction({ action }) {
  return (
    <Section title="Suggested Action">
      <div
        style={{
          padding: '12px 14px',
          borderRadius: 8,
          background: 'var(--color-accent-subtle)',
          border: '1px solid var(--color-accent)',
          fontSize: 12,
          color: 'var(--color-text-primary)',
          lineHeight: 1.5,
          fontWeight: 500,
        }}
      >
        {action}
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

function Footer({ onClose }) {
  return (
    <div
      style={{
        padding: '12px 20px',
        borderTop: '1px solid var(--color-border)',
        display: 'flex',
        gap: 8,
      }}
    >
      <button
        style={{
          flex: 1,
          padding: '8px 12px',
          borderRadius: 8,
          border: 'none',
          background: 'var(--color-accent)',
          color: '#fff',
          fontSize: 13,
          fontWeight: 500,
          cursor: 'pointer',
          transition: 'opacity 0.15s ease',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.opacity = '0.85'; }}
        onMouseLeave={(e) => { e.currentTarget.style.opacity = '1'; }}
      >
        Acknowledge
      </button>
      <button
        style={{
          flex: 1,
          padding: '8px 12px',
          borderRadius: 8,
          border: '1px solid var(--color-border)',
          background: 'transparent',
          color: 'var(--color-text-secondary)',
          fontSize: 13,
          fontWeight: 500,
          cursor: 'pointer',
          transition: 'all 0.15s ease',
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
        Assign
      </button>
      <button
        onClick={onClose}
        style={{
          flex: 1,
          padding: '8px 12px',
          borderRadius: 8,
          border: '1px solid var(--color-border)',
          background: 'transparent',
          color: 'var(--color-text-secondary)',
          fontSize: 13,
          fontWeight: 500,
          cursor: 'pointer',
          transition: 'all 0.15s ease',
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
        Export
      </button>
    </div>
  );
}
