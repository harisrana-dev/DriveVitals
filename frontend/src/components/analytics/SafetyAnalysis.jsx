import { memo, useMemo } from 'react';
import {
  BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

const chartTipStyle = {
  background: 'var(--color-tooltip-bg, #1e293b)',
  border: '1px solid var(--color-border)',
  borderRadius: 8,
  padding: '8px 12px',
  fontSize: 11,
  color: 'var(--color-tooltip-text, #f8fafc)',
};

function ChartTip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div style={chartTipStyle}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ color: p.color, display: 'flex', justifyContent: 'space-between', gap: 16 }}>
          <span>{p.name}</span>
          <span style={{ fontWeight: 600 }}>{p.value}</span>
        </div>
      ))}
    </div>
  );
}

function formatDateLabel(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

const EVENT_TYPE_LABELS = {
  speeding: 'Speeding',
  harsh_braking: 'Harsh Braking',
  aggressive_throttle: 'Aggressive Throttle',
  high_rpm: 'High RPM',
};

const EVENT_TYPE_COLORS = {
  speeding: 'var(--color-red)',
  harsh_braking: 'var(--color-amber)',
  aggressive_throttle: 'var(--color-purple, #8b5cf6)',
  high_rpm: 'var(--color-blue)',
};

export const SafetyAnalysis = memo(function SafetyAnalysis({ eventBreakdown, eventTrend }) {
  const breakdown = eventBreakdown?.breakdown || [];

  const trendData = useMemo(() => {
    if (!eventTrend?.trend) return [];
    return eventTrend.trend.map((d) => ({
      ...d,
      label: formatDateLabel(d.date),
    }));
  }, [eventTrend]);

  return (
    <div>
      <h2 style={{
        fontSize: 14,
        fontWeight: 700,
        color: 'var(--color-text-primary)',
        marginBottom: 12,
        letterSpacing: '-0.01em',
      }}>
        Safety & Event Analysis
      </h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 12 }}>
        {/* Event Breakdown */}
        <div style={{
          padding: '16px 20px',
          borderRadius: 14,
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
        }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 12 }}>
            Event Breakdown
          </h3>
          {breakdown.length > 0 ? (
            <>
              <div style={{
                fontSize: 22,
                fontWeight: 700,
                color: 'var(--color-text-primary)',
                marginBottom: 16,
              }}>
                {eventBreakdown.total_events?.toLocaleString() || '0'}
                <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--color-text-muted)', marginLeft: 6 }}>
                  total events
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {breakdown.map((b) => {
                  const pct = eventBreakdown.total_events > 0
                    ? (b.count / eventBreakdown.total_events) * 100
                    : 0;
                  return (
                    <div key={b.event_type}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                        <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-primary)' }}>
                          {EVENT_TYPE_LABELS[b.event_type] || b.event_type}
                        </span>
                        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                          {b.count} ({pct.toFixed(0)}%)
                        </span>
                      </div>
                      <div style={{
                        height: 6,
                        background: 'var(--color-surface-hover, rgba(0,0,0,0.03))',
                        borderRadius: 3,
                        overflow: 'hidden',
                      }}>
                        <div style={{
                          height: '100%',
                          width: `${pct}%`,
                          background: EVENT_TYPE_COLORS[b.event_type] || 'var(--color-accent)',
                          borderRadius: 3,
                        }} />
                      </div>
                      {b.rate_per_100km != null && (
                        <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginTop: 2 }}>
                          {b.rate_per_100km.toFixed(1)} / 100 km
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          ) : (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: 150,
              color: 'var(--color-text-muted)',
              fontSize: 13,
            }}>
              No events in this period
            </div>
          )}
        </div>

        {/* Event Trend */}
        <div style={{
          padding: '16px 20px',
          borderRadius: 14,
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
        }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 12 }}>
            Event Trend Over Time
          </h3>
          <div style={{ height: 260 }}>
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="speedGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--color-red)" stopOpacity={0.15} />
                      <stop offset="100%" stopColor="var(--color-red)" stopOpacity={0.01} />
                    </linearGradient>
                    <linearGradient id="brakeGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--color-amber)" stopOpacity={0.15} />
                      <stop offset="100%" stopColor="var(--color-amber)" stopOpacity={0.01} />
                    </linearGradient>
                    <linearGradient id="throttleGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--color-purple, #8b5cf6)" stopOpacity={0.15} />
                      <stop offset="100%" stopColor="var(--color-purple, #8b5cf6)" stopOpacity={0.01} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} minTickGap={40} />
                  <YAxis tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} width={35} />
                  <Tooltip content={<ChartTip />} />
                  <Legend wrapperStyle={{ fontSize: 10, color: 'var(--color-text-muted)' }} />
                  <Area type="monotone" dataKey="speeding" name="Speeding" stackId="1" stroke="var(--color-red)" fill="url(#speedGrad)" strokeWidth={1.5} />
                  <Area type="monotone" dataKey="harsh_braking" name="Harsh Braking" stackId="1" stroke="var(--color-amber)" fill="url(#brakeGrad)" strokeWidth={1.5} />
                  <Area type="monotone" dataKey="aggressive_throttle" name="Aggressive Throttle" stackId="1" stroke="var(--color-purple, #8b5cf6)" fill="url(#throttleGrad)" strokeWidth={1.5} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                color: 'var(--color-text-muted)',
                fontSize: 13,
              }}>
                No event trend data for this period
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
});
