import { useState } from 'react';
import { X, Check, AlertTriangle } from 'lucide-react';
import { useMaintenanceVehicle } from '../../hooks/useMaintenance';
import { useLiveData } from '../../context/useLiveData';
import { StatusBadge } from './StatusBadge';
import { PriorityBadge } from './PriorityBadge';
import { formatMaintenanceDue } from '../../utils/maintenance';
import { healthColor } from '../../utils/health';
import { drawerStackOffset, drawerZIndex, overlayZIndex } from '../../utils/drawerLayout';

export function MaintenanceDrawer({ vehicleId, onClose, onViewVehicle, depth = 0 }) {
  const right = drawerStackOffset(depth, 520);
  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.3)',
          zIndex: overlayZIndex(depth),
          animation: 'fadeIn 0.15s ease-out',
        }}
      />
      <div
        style={{
          position: 'fixed',
          top: 0,
          right,
          width: 520,
          maxWidth: '92vw',
          height: '100vh',
          background: 'var(--color-surface)',
          borderLeft: '1px solid var(--color-border)',
          boxShadow: 'var(--color-shadow-lg)',
          zIndex: drawerZIndex(depth),
          display: 'flex',
          flexDirection: 'column',
          animation: 'slideInRight 0.2s ease-out',
        }}
      >
        <DrawerContent vehicleId={vehicleId} onClose={onClose} onViewVehicle={onViewVehicle} />
      </div>
    </>
  );
}

function DrawerContent({ vehicleId, onClose, onViewVehicle }) {
  const { vehicle, workItems, completed, relatedAlerts, kpis } = useMaintenanceVehicle(vehicleId);

  return (
    <>
      <Header
        vehicle={vehicle}
        onClose={onClose}
        onViewVehicle={onViewVehicle}
      />
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
        <VehicleInfo vehicle={vehicle} kpis={kpis} />
        <PendingWork workItems={workItems} />
        {relatedAlerts.length > 0 && <RelatedAlerts alerts={relatedAlerts} />}
        <CompletedHistory completed={completed} />
      </div>
    </>
  );
}

function Header({ vehicle, onClose, onViewVehicle }) {
  if (!vehicle) {
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
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)' }}>
          Maintenance
        </div>
        <button onClick={onClose} aria-label="Close" style={closeBtn}>
          <X size={18} />
        </button>
      </div>
    );
  }

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
            background: 'var(--color-accent-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-accent)',
            fontSize: 14,
            fontWeight: 600,
            flexShrink: 0,
          }}
        >
          {(vehicle.vehicle_name || vehicle.vehicle_id).split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {vehicle.vehicle_name || vehicle.vehicle_id}
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
            {vehicle.vehicle_id} · {vehicle.driver_name || '\u2014'}
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {onViewVehicle && (
          <button
            onClick={() => onViewVehicle(vehicle.vehicle_id)}
            title="Open full vehicle profile"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              padding: '5px 10px',
              borderRadius: 8,
              border: '1px solid var(--color-border)',
              background: 'transparent',
              color: 'var(--color-text-secondary)',
              fontSize: 11,
              fontWeight: 500,
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
            Vehicle profile
          </button>
        )}
        <button onClick={onClose} aria-label="Close" style={closeBtn}>
          <X size={18} />
        </button>
      </div>
    </div>
  );
}

const closeBtn = {
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
};

function VehicleInfo({ vehicle, kpis }) {
  if (!vehicle) {
    return (
      <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
        Vehicle not found.
      </div>
    );
  }
  const score = vehicle.overall_health_score;
  const color = healthColor(score);
  const odometer = vehicle.odometer_km;

  return (
    <Section title="Vehicle Information">
      <div
        style={{
          padding: '16px 18px',
          borderRadius: 12,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
        }}
      >
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 14 }}>
          <div style={{ position: 'relative', width: 72, height: 72, flexShrink: 0 }}>
            <svg width={72} height={72} viewBox="0 0 72 72">
              <circle cx={36} cy={36} r={30} fill="none" stroke="var(--color-border-light)" strokeWidth={5} />
              <circle
                cx={36} cy={36} r={30} fill="none" stroke={color} strokeWidth={5}
                strokeDasharray={`${(score != null ? score / 100 : 0) * 188.5} 188.5`}
                strokeLinecap="round"
                transform="rotate(-90 36 36)"
                style={{ transition: 'stroke-dasharray 0.4s ease' }}
              />
              <text x={36} y={36} textAnchor="middle" dy="5" fontSize="16" fontWeight="700" fill="var(--color-text-primary)">
                {score != null ? Math.round(score) : '\u2014'}
              </text>
            </svg>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, justifyContent: 'center', minWidth: 0 }}>
            <span
              style={{
                display: 'inline-block',
                padding: '2px 8px',
                borderRadius: 4,
                background: color === 'var(--color-text-muted)' ? 'var(--color-surface-hover)' : `${color}1a`,
                color,
                fontSize: 10,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                alignSelf: 'flex-start',
              }}
            >
              {score != null ? (score >= 80 ? 'Healthy' : score >= 50 ? 'Warning' : 'Critical') : 'Unknown health'}
            </span>
            <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
              {vehicle.driver_name ? `Driver: ${vehicle.driver_name}` : '\u2014'}
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px', fontSize: 12 }}>
          <DetailRow label="Odometer" value={odometer != null ? `${odometer.toLocaleString()} km` : '\u2014'} />
          <DetailRow label="Work items" value={`${kpis.total} pending`} />
          <DetailRow label="Overdue" value={String(kpis.overdue)} />
          <DetailRow label="Due soon" value={String(kpis.dueSoon)} />
        </div>
      </div>
    </Section>
  );
}

function DetailRow({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <span style={{ color: 'var(--color-text-muted)' }}>{label}</span>
      <span style={{ color: 'var(--color-text-primary)', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>{value}</span>
    </div>
  );
}

function PendingWork({ workItems }) {
  const { completeMaintenance } = useLiveData();
  const [completing, setCompleting] = useState(null);
  const [error, setError] = useState(null);

  const handleComplete = async (item) => {
    setError(null);
    setCompleting(item.id);
    try {
      await completeMaintenance(item.id, item.odometer_km);
    } catch {
      setError(`Could not complete "${item.maintenanceTypeLabel}" — the record may have changed.`);
    } finally {
      setCompleting(null);
    }
  };

  return (
    <Section title={`Pending Work${workItems.length ? ` (${workItems.length})` : ''}`}>
      {error && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            marginBottom: 8,
            padding: '8px 10px',
            borderRadius: 8,
            background: 'var(--color-red-bg)',
            color: 'var(--color-red)',
            fontSize: 11,
          }}
        >
          <AlertTriangle size={12} />
          {error}
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {workItems.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '6px 0' }}>
            No pending maintenance for this vehicle.
          </div>
        ) : (
          workItems.map((item) => (
            <WorkItemRow
              key={item.workKey}
              item={item}
              completing={completing === item.id}
              onComplete={() => handleComplete(item)}
            />
          ))
        )}
      </div>
    </Section>
  );
}

function WorkItemRow({ item, completing, onComplete }) {
  return (
    <div
      style={{
        padding: '12px 14px',
        borderRadius: 10,
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border-light)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
              {item.maintenanceTypeLabel}
            </span>
            <StatusBadge status={item.dueStatus} size="sm" />
            <PriorityBadge priority={item.priority} size="sm" />
            {item.projectionCount > 1 && (
              <span style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>
                {item.projectionCount} projections
              </span>
            )}
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginTop: 4, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <span>
              Due <strong style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{formatMaintenanceDue(item)}</strong>
            </span>
            {item.component && <span>{item.component}</span>}
          </div>
          {item.reason && (
            <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4 }}>
              {item.reason}
            </div>
          )}
          {item.recommended_action && (
            <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginTop: 2 }}>
              {item.recommended_action}
            </div>
          )}
        </div>
        <button
          onClick={onComplete}
          disabled={completing}
          title="Mark as completed"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            padding: '6px 10px',
            borderRadius: 6,
            border: '1px solid var(--color-accent)',
            background: 'transparent',
            color: 'var(--color-accent)',
            fontSize: 11,
            fontWeight: 600,
            cursor: 'pointer',
            fontFamily: 'inherit',
            lineHeight: 1,
            whiteSpace: 'nowrap',
            transition: 'all 0.12s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-accent-subtle)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
          }}
        >
          <Check size={12} />
          {completing ? 'Completing' : 'Complete'}
        </button>
      </div>
    </div>
  );
}

function RelatedAlerts({ alerts }) {
  return (
    <Section title={`Related Alerts (${alerts.length})`}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {alerts.slice(0, 5).map((a) => (
          <div
            key={a.alert_id}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '9px 12px',
              borderRadius: 8,
              background: 'var(--color-bg)',
              border: '1px solid var(--color-border-light)',
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                background: a.severity === 'critical' ? 'var(--color-red)' : a.severity === 'high' ? 'var(--color-amber)' : 'var(--color-blue)',
                flexShrink: 0,
              }}
            />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {a.alert_type || a.category || 'Maintenance'}
              </div>
              <div style={{ fontSize: 11, color: 'var(--color-text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {a.message || a.condition || '\u2014'}
              </div>
            </div>
            <span
              style={{
                flexShrink: 0,
                fontSize: 10,
                fontWeight: 600,
                padding: '1px 6px',
                borderRadius: 3,
                background: 'var(--color-surface-hover)',
                color: 'var(--color-text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              {a.status}
            </span>
          </div>
        ))}
      </div>
    </Section>
  );
}

function CompletedHistory({ completed }) {
  return (
    <Section title={`Service History${completed.length ? ` (${completed.length})` : ''}`}>
      <div
        style={{
          padding: '14px 16px',
          borderRadius: 8,
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border-light)',
        }}
      >
        {completed.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            No completed service records for this vehicle.
          </div>
        ) : (
          completed.slice(0, 8).map((h, i) => (
            <div
              key={h.id || `${h.maintenance_type}-${h.completed_at}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '6px 0',
                borderBottom: i < completed.length - 1 ? '1px solid var(--color-border-light)' : 'none',
              }}
            >
              <div
                style={{
                  width: 2,
                  height: 28,
                  borderRadius: 1,
                  background: 'var(--color-accent)',
                  flexShrink: 0,
                }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-primary)' }}>
                  {h.maintenanceTypeLabel}
                </div>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                  {h.completed_at ? new Date(h.completed_at).toLocaleString() : '\u2014'}
                </div>
              </div>
              <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                {h.completed_odometer_km != null ? `${h.completed_odometer_km.toLocaleString()} km` : '\u2014'}
              </span>
            </div>
          ))
        )}
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
