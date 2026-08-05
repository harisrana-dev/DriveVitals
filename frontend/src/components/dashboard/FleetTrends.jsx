import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { useTelemetryData } from '../../hooks/useFleetData';

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--chart-tooltip-bg)',
      color: 'var(--chart-tooltip-text)',
      padding: '8px 12px',
      borderRadius: 8,
      fontSize: 12,
      boxShadow: 'var(--color-shadow-md)',
      border: '1px solid var(--color-border)',
    }}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
      {payload.map((p) => (
        <div key={p.name} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 6, height: 6, borderRadius: 3, background: p.name === 'fuelEfficiency' ? 'var(--color-accent)' : 'var(--color-green)' }} />
          <span style={{ color: 'var(--color-text-secondary)' }}>{p.name === 'fuelEfficiency' ? 'Fuel Eff.' : 'Safety'}:</span>
          <span style={{ fontWeight: 500 }}>{p.value}{p.name === 'fuelEfficiency' ? ' km/L' : ''}</span>
        </div>
      ))}
    </div>
  );
}

export function FleetTrends() {
  const data = useTelemetryData();

  return (
    <div className="two-col-grid">
      <div className="fade-in stagger-4" style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
      }}>
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 2 }}>
            Fuel Efficiency Trend
          </h3>
          <p style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            Fleet average km/L over 12 hours
          </p>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="fuelGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-accent)" stopOpacity={0.15} />
                <stop offset="100%" stopColor="var(--color-accent)" stopOpacity={0.01} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" />
            <XAxis dataKey="time" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} padding={{ top: 12, bottom: 8 }} />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="fuelEfficiency"
              stroke="var(--color-accent)"
              strokeWidth={2}
              fill="url(#fuelGrad)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="fade-in stagger-5" style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
      }}>
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 2 }}>
            Fleet Safety Trend
          </h3>
          <p style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            Aggregate safety score over 12 hours
          </p>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" />
            <XAxis dataKey="time" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} padding={{ top: 12, bottom: 8 }} />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="safetyScore"
              stroke="var(--color-green)"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: 'var(--color-green)' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
