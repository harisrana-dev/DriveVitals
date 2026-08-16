import { memo } from 'react';
import { Layers } from 'lucide-react';

const STATUS_META = {
  overdue: { color: 'var(--color-red)' },
  dueSoon: { color: 'var(--color-amber)' },
  scheduled: { color: 'var(--color-blue)' },
  future: { color: 'var(--color-green)' },
};

export const ServiceWorkloadPanel = memo(function ServiceWorkloadPanel({ workload, onTypeSelect, activeType }) {
  const list = Array.isArray(workload) ? workload : [];
  const maxTotal = Math.max(...list.map((w) => w.total), 1);

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
        flex: 1,
        minWidth: 0,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
        <Layers size={14} style={{ color: 'var(--color-blue)' }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
          Service Workload
        </span>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 4 }}>
          pending work by service type
        </span>
      </div>
      <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 10 }}>
        Click a service type to filter the work queue
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {list.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '8px 0' }}>
            No pending work items.
          </div>
        ) : (
          list.map((w) => {
            const active = activeType === w.maintenance_type;
            const totalPct = (w.total / maxTotal) * 100;
            return (
              <div key={w.maintenance_type}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 4 }}>
                  <button
                    onClick={() => onTypeSelect && onTypeSelect(w.maintenance_type)}
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: 0,
                      cursor: 'pointer',
                      fontFamily: 'inherit',
                      fontSize: 12,
                      fontWeight: active ? 700 : 500,
                      color: active ? 'var(--color-accent)' : 'var(--color-text-primary)',
                      textAlign: 'left',
                    }}
                  >
                    {w.label}
                  </button>
                  <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
                    {w.total}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ flex: 1, height: 4, borderRadius: 2, background: 'var(--color-border-light)', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${totalPct}%`, background: 'var(--color-accent)', borderRadius: 2 }} />
                  </div>
                  <span style={{ fontSize: 10, color: 'var(--color-text-muted)', whiteSpace: 'nowrap', fontVariantNumeric: 'tabular-nums' }}>
                    {[
                      w.overdue > 0 ? `${w.overdue} overdue` : null,
                      w.dueSoon > 0 ? `${w.dueSoon} due soon` : null,
                      w.scheduled > 0 ? `${w.scheduled} scheduled` : null,
                    ].filter(Boolean).join(' · ') || `${w.future} future`}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 2, marginTop: 3 }}>
                  {(['overdue', 'dueSoon', 'scheduled', 'future']).map((k) =>
                    w[k] > 0 ? (
                      <span
                        key={k}
                        style={{
                          display: 'block',
                          height: 3,
                          flex: w[k],
                          background: STATUS_META[k].color,
                          opacity: active ? 1 : 0.7,
                          borderRadius: 2,
                        }}
                        title={k}
                      />
                    ) : null
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
});
