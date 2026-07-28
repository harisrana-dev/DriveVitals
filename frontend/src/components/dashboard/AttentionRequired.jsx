import { useState } from 'react';
import { AlertTriangle, Clock, User, ChevronRight, Check } from 'lucide-react';
import { useAlerts } from '../../hooks/useFleetData';

const severityConfig = {
  critical: { bg: 'var(--color-red-light)', color: 'var(--color-red)', border: 'var(--color-red)', label: 'Critical' },
  warning: { bg: 'var(--color-amber-light)', color: 'var(--color-amber)', border: 'var(--color-amber)', label: 'Warning' },
  info: { bg: 'var(--color-accent-light)', color: 'var(--color-accent)', border: 'var(--color-accent)', label: 'Info' },
};

export function AttentionRequired() {
  const initialAlerts = useAlerts();
  const [alertList, setAlertList] = useState(initialAlerts);

  const handleAcknowledge = (id) => {
    setAlertList((prev) => prev.map((a) => a.id === id ? { ...a, acknowledged: true } : a));
  };

  return (
    <div className="fade-in stagger-3" style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 12,
      overflow: 'hidden',
    }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border-light)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 2 }}>
              Attention Required
            </h3>
            <p style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
              {alertList.filter((a) => !a.acknowledged).length} unacknowledged alerts
            </p>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {alertList.map((alert, i) => {
          const sev = severityConfig[alert.severity];
          return (
            <div
              key={alert.id}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 12,
                padding: '14px 20px',
                borderBottom: i < alertList.length - 1 ? '1px solid var(--color-border-light)' : 'none',
                opacity: alert.acknowledged ? 0.5 : 1,
                transition: 'opacity 0.2s ease',
              }}
            >
              <div style={{
                width: 32,
                height: 32,
                borderRadius: 8,
                background: sev.bg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: sev.color,
                flexShrink: 0,
                marginTop: 2,
              }}>
                {alert.severity === 'critical' && <AlertTriangle size={16} />}
                {alert.severity === 'warning' && <Clock size={16} />}
                {alert.severity === 'info' && <User size={16} />}
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                  <span style={{
                    fontSize: 10,
                    fontWeight: 600,
                    padding: '1px 6px',
                    borderRadius: 4,
                    background: sev.bg,
                    color: sev.color,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}>
                    {sev.label}
                  </span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                    {alert.vehicleId}
                  </span>
                  {alert.driverName && (
                    <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                      \u00b7 {alert.driverName}
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-text-primary)', marginBottom: 2 }}>
                  {alert.title}
                </div>
                <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 4 }}>
                  {alert.description}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: 'var(--color-text-muted)' }}>
                  {alert.value && <span>{alert.value}</span>}
                  {alert.threshold && <span>\u00b7 Threshold: {alert.threshold}</span>}
                  <span>\u00b7 {alert.timestamp}</span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 6, flexShrink: 0, marginTop: 2 }}>
                {!alert.acknowledged && (
                  <button
                    onClick={() => handleAcknowledge(alert.id)}
                    style={{
                      padding: '5px 10px',
                      borderRadius: 6,
                      border: '1px solid var(--color-border)',
                      fontSize: 12,
                      fontWeight: 500,
                      color: 'var(--color-text-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      transition: 'all 0.15s ease',
                      whiteSpace: 'nowrap',
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
                    <Check size={12} />
                    Ack
                  </button>
                )}
                <button
                  style={{
                    padding: '5px 10px',
                    borderRadius: 6,
                    background: alert.acknowledged ? 'var(--color-surface-hover)' : 'var(--color-accent)',
                    color: alert.acknowledged ? 'var(--color-text-muted)' : '#fff',
                    fontSize: 12,
                    fontWeight: 500,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                    transition: 'all 0.15s ease',
                    whiteSpace: 'nowrap',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.opacity = '0.85';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.opacity = '1';
                  }}
                >
                  {alert.actionLabel}
                  <ChevronRight size={12} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
