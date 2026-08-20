import { memo, useMemo } from 'react';
import {
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { User } from 'lucide-react';

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
          <span style={{ fontWeight: 600 }}>{p.value != null ? Number(p.value).toFixed(2) : '—'}</span>
        </div>
      ))}
    </div>
  );
}

function formatDateLabel(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function EmptyState({ message }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: 200,
      color: 'var(--color-text-muted)',
      fontSize: 13,
    }}>
      {message}
    </div>
  );
}

export const DriverIntelligence = memo(function DriverIntelligence({
  driverRanking,
  driverTrend,
  selectedDriverId,
  onSelectDriver,
}) {
  const drivers = driverRanking?.drivers || [];

  const trendData = useMemo(() => {
    if (!driverTrend?.observations) return [];
    return driverTrend.observations.map((o) => ({
      ...o,
      label: formatDateLabel(o.date),
    }));
  }, [driverTrend]);

  return (
    <div>
      <h2 style={{
        fontSize: 14,
        fontWeight: 700,
        color: 'var(--color-text-primary)',
        marginBottom: 12,
        letterSpacing: '-0.01em',
      }}>
        Driver Intelligence
      </h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        {/* Driver Ranking Table */}
        <div style={{
          padding: '16px 20px',
          borderRadius: 14,
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          overflow: 'auto',
        }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 12 }}>
            Driver Performance Ranking
          </h3>
          {drivers.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                  {['Driver', 'Safety', 'Trips', 'Events/100km', 'Fuel Eff.'].map((h) => (
                    <th key={h} style={{
                      padding: '6px 8px',
                      textAlign: 'left',
                      fontSize: 10,
                      fontWeight: 600,
                      color: 'var(--color-text-muted)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {drivers.map((d) => {
                  const isSelected = selectedDriverId === d.driver_id;
                  return (
                    <tr
                      key={d.driver_id}
                      onClick={() => onSelectDriver(isSelected ? null : d.driver_id)}
                      style={{
                        cursor: 'pointer',
                        background: isSelected ? 'var(--color-accent-subtle)' : 'transparent',
                        borderBottom: '1px solid var(--color-border-light, var(--color-border))',
                        transition: 'background 0.1s ease',
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected) e.currentTarget.style.background = 'var(--color-surface-hover)';
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected) e.currentTarget.style.background = 'transparent';
                      }}
                    >
                      <td style={{ padding: '8px', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{
                            width: 28,
                            height: 28,
                            borderRadius: 7,
                            background: 'var(--color-accent-subtle)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                          }}>
                            <User size={13} style={{ color: 'var(--color-accent)' }} />
                          </div>
                          <div>
                            <div style={{ fontSize: 12, fontWeight: 600 }}>{d.driver_name}</div>
                            <div style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>{d.driver_id}</div>
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: '8px', fontWeight: 600, color: d.safety_score != null ? 'var(--color-text-primary)' : 'var(--color-text-muted)' }}>
                        {d.safety_score != null ? `${d.safety_score}` : '—'}
                      </td>
                      <td style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>
                        {d.completed_trips}
                      </td>
                      <td style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>
                        {d.event_rate != null ? d.event_rate.toFixed(1) : '—'}
                      </td>
                      <td style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>
                        {d.fuel_efficiency != null ? `${d.fuel_efficiency} km/L` : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <EmptyState message="No driver data available" />
          )}
        </div>

        {/* Driver Trend + Safety Distribution */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{
            padding: '16px 20px',
            borderRadius: 14,
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            flex: 1,
          }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 4 }}>
              {driverTrend ? `Performance Trend — ${driverTrend.driver_name}` : 'Select a Driver'}
            </h3>
            <p style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 12 }}>
              {driverTrend
                ? (driverTrend.data_quality === 'insufficient'
                  ? driverTrend.context
                  : 'Trip safety scores over time')
                : 'Click a driver row to view their performance trend'}
            </p>
            <div style={{ height: 200 }}>
              {trendData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                    <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} minTickGap={40} />
                    <YAxis tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} domain={[0, 100]} width={35} />
                    <Tooltip content={<ChartTip />} />
                    <Line type="monotone" dataKey="score" name="Safety Score" stroke="var(--color-accent)" strokeWidth={1.8} dot={{ r: 3, fill: 'var(--color-accent)' }} connectNulls />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState message={driverTrend ? 'No completed trips in this period' : 'Select a driver above'} />
              )}
            </div>
          </div>

          {/* Safety Score Distribution */}
          <SafetyDistribution distribution={driverRanking?.drivers} />
        </div>
      </div>
    </div>
  );
});

function SafetyDistribution({ distribution }) {
  const buckets = useMemo(() => {
    if (!distribution || distribution.length < 2) return null;
    const scored = distribution.filter((d) => d.safety_score != null);
    if (scored.length < 2) return null;

    const ranges = [
      { label: '90–100', min: 90, max: 101 },
      { label: '80–89', min: 80, max: 90 },
      { label: '70–79', min: 70, max: 80 },
      { label: '60–69', min: 60, max: 70 },
      { label: '< 60', min: 0, max: 60 },
    ];

    return ranges.map((r) => ({
      ...r,
      count: scored.filter((d) => d.safety_score >= r.min && d.safety_score < r.max).length,
    }));
  }, [distribution]);

  if (!buckets) return null;

  const maxCount = Math.max(...buckets.map((b) => b.count), 1);

  return (
    <div style={{
      padding: '16px 20px',
      borderRadius: 14,
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
    }}>
      <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 12 }}>
        Safety Score Distribution
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {buckets.map((b) => (
          <div key={b.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', width: 44, textAlign: 'right', fontWeight: 500 }}>
              {b.label}
            </span>
            <div style={{ flex: 1, height: 18, background: 'var(--color-surface-hover, rgba(0,0,0,0.03))', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{
                height: '100%',
                width: `${(b.count / maxCount) * 100}%`,
                background: 'var(--color-accent)',
                borderRadius: 4,
                minWidth: b.count > 0 ? 4 : 0,
                transition: 'width 0.3s ease',
              }} />
            </div>
            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-primary)', width: 20, textAlign: 'right' }}>
              {b.count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
