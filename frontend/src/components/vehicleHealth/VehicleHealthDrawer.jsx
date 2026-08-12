import { Link } from 'react-router-dom';
import { X, Wrench } from 'lucide-react';
import { useVehicle } from '../../hooks/useVehicleHealth';
import { useLiveData } from '../../context/LiveDataContext';
import {
  canonicalHealthCategory,
  healthColor,
  healthLabel,
  componentLabel,
  normalizeHealthReasons,
  HEALTH_SEVERITY_COLORS,
  HEALTH_SEVERITY_LABEL,
} from '../../utils/health';
import { dueStatus, dueStatusStyle } from '../../utils/maintenance';

const COMPONENT_KEYS = ['engine', 'cooling', 'braking', 'transmission', 'fuel'];

const MAINTENANCE_TYPE_LABELS = {
  oil_change: 'Oil Change',
  brake_inspection: 'Brake Inspection',
  tyre_rotation: 'Tyre Rotation',
  coolant: 'Coolant',
  general_inspection: 'General Inspection',
};

function titleCase(value) {
  if (!value) return 'Service';
  return String(value).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function getLoadState(value) {
  if (value == null) return { label: 'Normal', severity: 'info' };
  if (value >= 85) return { label: 'Critical', severity: 'critical' };
  if (value >= 70) return { label: 'High', severity: 'warning' };
  if (value >= 50) return { label: 'Moderate', severity: 'warning' };
  return { label: 'Normal', severity: 'info' };
}

function getFuelState(value) {
  if (value == null) return { label: 'Normal', severity: 'info' };
  if (value <= 20) return { label: 'Low', severity: 'critical' };
  if (value <= 40) return { label: 'Moderate', severity: 'warning' };
  return { label: 'Good', severity: 'info' };
}

function getRpmState(value, redline) {
  if (value == null) return { label: 'Normal', severity: 'info' };
  if (value >= (redline || 6200)) return { label: 'Critical', severity: 'critical' };
  if (value >= 5000) return { label: 'Elevated', severity: 'warning' };
  return { label: 'Normal', severity: 'info' };
}

function getTempState(value, overheat) {
  if (value == null) return { label: 'Normal', severity: 'info' };
  if (value >= (overheat || 100)) return { label: 'Critical', severity: 'critical' };
  if (value >= 92) return { label: 'Elevated', severity: 'warning' };
  return { label: 'Normal', severity: 'info' };
}

function formatEvidence(evidence) {
  if (!evidence || typeof evidence !== 'object') return null;
  const parts = [];
  if (evidence.event_count != null) parts.push(`${evidence.event_count} events`);
  if (evidence.percent != null) parts.push(`${evidence.percent.toFixed(1)}%`);
  if (evidence.window_fraction != null) parts.push(`${(evidence.window_fraction * 100).toFixed(0)}% of window`);
  if (evidence.temperature_c != null) parts.push(`${evidence.temperature_c.toFixed(0)}\u00b0C`);
  if (evidence.stddev_c != null) parts.push(`stddev ${evidence.stddev_c.toFixed(1)}\u00b0C`);
  if (evidence.rpm != null) parts.push(`${Math.round(evidence.rpm)} rpm`);
  if (evidence.speed_kmh != null) parts.push(`${evidence.speed_kmh.toFixed(0)} km/h`);
  if (evidence.efficiency_km_per_l != null) parts.push(`${evidence.efficiency_km_per_l.toFixed(1)} km/L`);
  if (evidence.throttle_percent != null) parts.push(`throttle ${evidence.throttle_percent.toFixed(0)}%`);
  if (evidence.mean_load_percent != null) parts.push(`mean load ${evidence.mean_load_percent.toFixed(0)}%`);
  return parts.join(' \u00b7 ');
}

function StateBadge({ label, severity }) {
  const color = severity === 'critical' ? 'var(--color-red)' : severity === 'warning' ? 'var(--color-amber)' : 'var(--color-green)';
  const bg = severity === 'critical' ? 'var(--color-red-bg)' : severity === 'warning' ? 'var(--color-amber-bg)' : 'var(--color-green-bg)';
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 8px',
        borderRadius: 4,
        background: bg,
        color,
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: '0.02em',
      }}
    >
      {label}
    </span>
  );
}

function SeverityDot({ severity }) {
  const color = severity === 'critical' ? 'var(--color-red)' : severity === 'warning' ? 'var(--color-amber)' : 'var(--color-blue)';
  return (
    <span
      aria-hidden="true"
      style={{
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: color,
        flexShrink: 0,
      }}
    />
  );
}

function AttentionItem({ reason }) {
  const severityColor = HEALTH_SEVERITY_COLORS[reason.severity] || 'var(--color-amber)';
  const severityBg = reason.severity === 'critical' ? 'var(--color-red-bg)' : 'var(--color-amber-bg)';
  const severityLabel = HEALTH_SEVERITY_LABEL[reason.severity] || 'Warning';
  const evidence = formatEvidence(reason.evidence);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        padding: '14px 16px',
        borderRadius: 10,
        background: severityBg,
        border: `1px solid ${severityColor}`,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <SeverityDot severity={reason.severity} />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', flex: 1 }}>
          {reason.title || reason.reason}
        </span>
        <span
          style={{
            fontSize: 10,
            fontWeight: 600,
            color: severityColor,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}
        >
          {severityLabel}
        </span>
      </div>

      {reason.summary && (
        <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', lineHeight: 1.5, paddingLeft: 14 }}>
          {reason.summary}
        </div>
      )}

      {evidence && (
        <div style={{ fontSize: 11, color: 'var(--color-text-muted)', paddingLeft: 14, fontVariantNumeric: 'tabular-nums' }}>
          Evidence: {evidence}
        </div>
      )}

      {reason.impact && (
        <div style={{ fontSize: 11, color: 'var(--color-text-muted)', paddingLeft: 14 }}>
          Impact: {reason.impact}
        </div>
      )}

      {reason.recommendation && (
        <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', paddingLeft: 14, fontStyle: 'italic' }}>
          Recommendation: {reason.recommendation}
        </div>
      )}
    </div>
  );
}

export function VehicleHealthDrawer({ vehicleId, onClose }) {
  const vehicle = useVehicle(vehicleId);
  if (!vehicle) return null;

  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.4)',
          zIndex: 300,
          animation: 'fadeIn 0.15s ease-out',
        }}
      />
      <div
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          width: 520,
          maxWidth: '92vw',
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
        <DrawerContent vehicle={vehicle} onClose={onClose} />
      </div>
    </>
  );
}

function DrawerContent({ vehicle, onClose }) {
  const { maintenance, healthConfig } = useLiveData();

  const reasons = normalizeHealthReasons(vehicle.healthReasons);
  const hasScore = vehicle.overallHealth != null;
  const cat = canonicalHealthCategory(vehicle.overallHealth, vehicle.healthStatus);
  const scoreLabel = healthLabel(cat);

  const attentionReasons = reasons.filter((r) => r.severity === 'critical' || r.severity === 'warning');
  const criticalReasons = attentionReasons.filter((r) => r.severity === 'critical');

  const vehicleMaintenance = (maintenance || [])
    .filter((m) => m.vehicle_id === vehicle.id && m.status !== 'completed')
    .map((m) => {
      const remainingKm = m.due_odometer_km != null && vehicle.odometer != null
        ? Math.max(0, Math.round(m.due_odometer_km - vehicle.odometer))
        : null;
      return {
        id: m.maintenance_id,
        type: MAINTENANCE_TYPE_LABELS[m.maintenance_type] || titleCase(m.maintenance_type),
        maintenanceType: m.maintenance_type,
        dueKm: m.due_odometer_km,
        remainingKm,
        dueStatus: remainingKm != null ? dueStatus(remainingKm) : null,
        style: remainingKm != null ? dueStatusStyle(dueStatus(remainingKm)) : null,
        priority: m.priority,
      };
    })
    .sort((a, b) => {
      const order = { critical: 0, high: 1, medium: 2, low: 3 };
      return (order[a.priority] ?? 4) - (order[b.priority] ?? 4);
    });

  const engine = healthConfig?.engine || {};
  const cooling = healthConfig?.cooling || {};

  return (
    <>
      <Header vehicle={vehicle} onClose={onClose} cat={cat} />

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px 24px',
          display: 'flex',
          flexDirection: 'column',
          gap: 24,
        }}
      >
        <HealthScoreCard
          score={vehicle.overallHealth}
          cat={cat}
          scoreColor={healthColor(cat)}
          scoreLabel={scoreLabel}
          hasScore={hasScore}
        />

        <Section title="Health Overview">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {COMPONENT_KEYS.map((key) => {
              const score = vehicle.components[key];
              const status = vehicle.componentsStatus[key];
              const componentCat = canonicalHealthCategory(score, status);
              const color = healthColor(componentCat);
              const label = healthLabel(componentCat);
              return (
                <div
                  key={key}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '10px 12px',
                    borderRadius: 8,
                    background: 'var(--color-bg)',
                    border: '1px solid var(--color-border-light)',
                  }}
                >
                  <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-secondary)', width: 100, flexShrink: 0 }}>
                    {componentLabel(key)}
                  </span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', width: 40, fontVariantNumeric: 'tabular-nums', textAlign: 'right' }}>
                    {score != null ? `${Math.round(score)}%` : '\u2014'}
                  </span>
                  <div style={{ flex: 1, height: 6, borderRadius: 3, background: 'var(--color-border-light)', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${score != null ? Math.max(0, Math.min(100, score)) : 0}%`,
                        height: '100%',
                        borderRadius: 3,
                        background: color,
                        transition: 'background-color 0.4s ease, width 0.4s ease',
                      }}
                    />
                  </div>
                  <span style={{ fontSize: 11, fontWeight: 500, color, width: 52, textAlign: 'right', textTransform: 'capitalize' }}>
                    {label}
                  </span>
                </div>
              );
            })}
          </div>
        </Section>

        {attentionReasons.length > 0 && (
          <Section title={criticalReasons.length > 0 ? 'Critical Issues' : 'Attention'}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {attentionReasons.slice(0, 5).map((reason, i) => (
                <AttentionItem key={`${reason.code}-${i}`} reason={reason} />
              ))}
            </div>
          </Section>
        )}

        <Section title="Current Condition">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <ConditionRow label="Coolant" value={vehicle.coolantTemp} unit="\u00b0C" getState={(v) => getTempState(v, cooling.overheat_temp_c)} />
            <ConditionRow label="Engine load" value={vehicle.engineLoad} unit="%" getState={getLoadState} />
            <ConditionRow label="RPM" value={vehicle.rpm} unit="" getState={(v) => getRpmState(v, engine.redline_rpm)} />
            <ConditionRow label="Fuel" value={vehicle.fuelLevel} unit="%" getState={getFuelState} />
          </div>
        </Section>

        <Section title="Maintenance">
          {vehicleMaintenance.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {vehicleMaintenance.slice(0, 4).map((item) => (
                <Link
                  key={item.id}
                  to={`/maintenance?vehicle=${encodeURIComponent(vehicle.id)}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 8,
                    padding: '10px 12px',
                    borderRadius: 8,
                    background: 'var(--color-bg)',
                    border: '1px solid var(--color-border-light)',
                    fontSize: 12,
                    textDecoration: 'none',
                    transition: 'border-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-accent)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border-light)'; }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
                    <Wrench size={13} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
                    <span style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>{item.type}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                    {item.remainingKm != null && (
                      <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                        {item.remainingKm.toLocaleString()} km
                      </span>
                    )}
                    {item.dueStatus ? (
                      <span
                        style={{
                          ...item.style,
                          padding: '2px 8px',
                          borderRadius: 4,
                          fontSize: 10,
                          fontWeight: 600,
                        }}
                      >
                        {item.dueStatus}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--color-text-muted)', fontSize: 11 }}>No odometer</span>
                    )}
                  </div>
                </Link>
              ))}
              {vehicleMaintenance.length > 4 && (
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)', paddingLeft: 4 }}>
                  +{vehicleMaintenance.length - 4} more scheduled service{vehicleMaintenance.length - 4 > 1 ? 's' : ''}
                </div>
              )}
            </div>
          ) : (
            <div
              style={{
                padding: '14px 16px',
                borderRadius: 8,
                background: 'var(--color-bg)',
                border: '1px solid var(--color-border-light)',
                fontSize: 12,
                color: 'var(--color-text-muted)',
              }}
            >
              No scheduled maintenance for this vehicle.
            </div>
          )}
          <div style={{ marginTop: 10 }}>
            <Link
              to={`/maintenance?vehicle=${encodeURIComponent(vehicle.id)}`}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                fontSize: 12,
                fontWeight: 500,
                color: 'var(--color-accent)',
                textDecoration: 'none',
              }}
            >
              Open Maintenance
              <span aria-hidden="true" style={{ fontSize: 14 }}>\u2192</span>
            </Link>
          </div>
        </Section>
      </div>

      <Footer onClose={onClose} />
    </>
  );
}

function HealthScoreCard({ score, cat, scoreColor, scoreLabel, hasScore }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 20,
        padding: '18px 20px',
        borderRadius: 12,
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border-light)',
      }}
    >
      <div style={{ position: 'relative', width: 96, height: 96, flexShrink: 0 }}>
        <svg width={96} height={96} viewBox="0 0 96 96">
          <circle cx={48} cy={48} r={40} fill="none" stroke="var(--color-border-light)" strokeWidth={6} />
          <circle
            cx={48}
            cy={48}
            r={40}
            fill="none"
            stroke={hasScore ? scoreColor : 'var(--color-border)'}
            strokeWidth={6}
            strokeDasharray={hasScore ? `${(score / 100) * 251.3} 251.3` : `0 251.3`}
            strokeLinecap="round"
            transform="rotate(-90 48 48)"
            style={{ transition: 'stroke-dasharray 0.4s ease' }}
          />
          <text x={48} y={48} textAnchor="middle" dy="5" fontSize="22" fontWeight="700" fill="var(--color-text-primary)">
            {hasScore ? Math.round(score) : '\u2014'}
          </text>
          <text x={48} y={48} textAnchor="middle" dy="22" fontSize="9" fontWeight="500" fill="var(--color-text-muted)">
            / 100
          </text>
        </svg>
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '4px 10px',
              borderRadius: 6,
              background: scoreColor,
              color: '#fff',
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            {scoreLabel}
          </span>
        </div>
        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
          {cat === 'healthy'
            ? 'Vehicle is operating normally. No critical issues detected.'
            : cat === 'warning'
              ? 'Vehicle requires attention. Review the issues below.'
              : cat === 'critical'
                ? 'Vehicle requires immediate attention. Critical issues detected.'
                : 'Health data unavailable for this vehicle.'}
        </div>
      </div>
    </div>
  );
}

function ConditionRow({ label, value, unit, getState }) {
  const state = getState(value);
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 12px',
        borderRadius: 8,
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border-light)',
      }}
    >
      <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', fontWeight: 500 }}>{label}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums', minWidth: 60, textAlign: 'right' }}>
          {value != null ? `${value.toFixed ? value.toFixed(1) : value}${unit}` : '\u2014'}
        </span>
        <StateBadge label={state.label} severity={state.severity} />
      </div>
    </div>
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
          marginBottom: 10,
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
        }}
      >
        {title}
      </div>
      {children}
    </div>
  );
}

function Header({ vehicle, onClose, cat }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '16px 24px',
        borderBottom: '1px solid var(--color-border)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: 10,
            background: 'var(--color-accent-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-accent)',
            fontSize: 14,
            fontWeight: 700,
            flexShrink: 0,
          }}
        >
          {vehicle.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
        </div>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)', lineHeight: 1.3 }}>
            {vehicle.name}
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'monospace', display: 'flex', alignItems: 'center', gap: 8, marginTop: 2 }}>
            <span>{vehicle.id}</span>
            <span style={{ color: 'var(--color-border)' }}>\u00b7</span>
            <span>{vehicle.driverName}</span>
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span
          aria-hidden="true"
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: cat === 'healthy' ? 'var(--color-green)' : cat === 'warning' ? 'var(--color-amber)' : cat === 'critical' ? 'var(--color-red)' : 'var(--color-text-muted)',
          }}
        />
        <button
          onClick={onClose}
          aria-label="Close vehicle health drawer"
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
    </div>
  );
}

function Footer({ onClose }) {
  return (
    <div
      style={{
        padding: '14px 24px',
        borderTop: '1px solid var(--color-border)',
        display: 'flex',
        gap: 8,
        justifyContent: 'flex-end',
      }}
    >
      <button
        onClick={onClose}
        style={{
          padding: '8px 16px',
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
        Close
      </button>
    </div>
  );
}
