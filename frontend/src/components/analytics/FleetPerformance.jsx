import { memo, useMemo } from 'react';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';

const chartTipStyle = {
  background: 'var(--color-tooltip-bg, #1e293b)',
  border: '1px solid var(--color-border)',
  borderRadius: 8,
  padding: '8px 12px',
  fontSize: 11,
  color: 'var(--color-tooltip-text, #f8fafc)',
};

function ChartTip({ active, payload, label, unit }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div style={chartTipStyle}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ color: p.color, display: 'flex', justifyContent: 'space-between', gap: 16 }}>
          <span>{p.name}</span>
          <span style={{ fontWeight: 600 }}>
            {p.value != null ? Number(p.value).toFixed(2) : '—'}{unit ? ` ${unit}` : ''}
          </span>
        </div>
      ))}
    </div>
  );
}

function ChartEmpty({ message }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: 200,
      color: 'var(--color-text-muted)',
      fontSize: 13,
    }}>
      {message || 'No data available'}
    </div>
  );
}

function ChartCard({ title, children, height = 220 }) {
  return (
    <div style={{
      padding: '16px 20px',
      borderRadius: 14,
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
    }}>
      <h3 style={{
        fontSize: 13,
        fontWeight: 600,
        color: 'var(--color-text-primary)',
        marginBottom: 12,
        lineHeight: 1.3,
      }}>
        {title}
      </h3>
      <div style={{ height }}>
        {children}
      </div>
    </div>
  );
}

function formatDateLabel(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export const FleetPerformance = memo(function FleetPerformance({ fleetTrend }) {
  const safetyData = useMemo(() => {
    if (!fleetTrend?.safety_score_trend) return [];
    return fleetTrend.safety_score_trend.map((d) => ({
      ...d,
      label: formatDateLabel(d.date),
    }));
  }, [fleetTrend]);

  const eventData = useMemo(() => {
    if (!fleetTrend?.event_rate_trend) return [];
    return fleetTrend.event_rate_trend.map((d) => ({
      ...d,
      label: formatDateLabel(d.date),
    }));
  }, [fleetTrend]);

  const fuelData = useMemo(() => {
    if (!fleetTrend?.fuel_efficiency_trend) return [];
    return fleetTrend.fuel_efficiency_trend.map((d) => ({
      ...d,
      label: formatDateLabel(d.date),
    }));
  }, [fleetTrend]);

  const tripData = useMemo(() => {
    if (!fleetTrend?.trip_count_trend) return [];
    return fleetTrend.trip_count_trend.map((d) => ({
      ...d,
      label: formatDateLabel(d.date),
    }));
  }, [fleetTrend]);

  return (
    <div>
      <h2 style={{
        fontSize: 14,
        fontWeight: 700,
        color: 'var(--color-text-primary)',
        marginBottom: 12,
        letterSpacing: '-0.01em',
      }}>
        Fleet Performance
      </h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 12 }}>
        <ChartCard title="Safety Score Trend" height={220}>
          {safetyData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={safetyData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="safetyGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-accent)" stopOpacity={0.15} />
                    <stop offset="100%" stopColor="var(--color-accent)" stopOpacity={0.01} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} minTickGap={40} />
                <YAxis tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} domain={[0, 100]} width={35} />
                <Tooltip content={<ChartTip unit="/ 100" />} />
                <Area type="monotone" dataKey="value" name="Safety Score" stroke="var(--color-accent)" strokeWidth={1.8} fill="url(#safetyGrad)" dot={{ r: 2, fill: 'var(--color-accent)' }} />
              </AreaChart>
            </ResponsiveContainer>
          ) : <ChartEmpty message="No safety score data for this period" />}
        </ChartCard>

        <ChartCard title="Event Rate (per 100 km)" height={220}>
          {eventData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={eventData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="eventGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-amber)" stopOpacity={0.15} />
                    <stop offset="100%" stopColor="var(--color-amber)" stopOpacity={0.01} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} minTickGap={40} />
                <YAxis tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} width={35} />
                <Tooltip content={<ChartTip unit="/ 100 km" />} />
                <Area type="monotone" dataKey="value" name="Event Rate" stroke="var(--color-amber)" strokeWidth={1.8} fill="url(#eventGrad)" dot={{ r: 2, fill: 'var(--color-amber)' }} />
              </AreaChart>
            </ResponsiveContainer>
          ) : <ChartEmpty message="No event data for this period" />}
        </ChartCard>

        <ChartCard title="Fuel Efficiency (km/L)" height={220}>
          {fuelData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={fuelData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} minTickGap={40} />
                <YAxis tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} width={35} />
                <Tooltip content={<ChartTip unit="km/L" />} />
                <Line type="monotone" dataKey="value" name="Fuel Efficiency" stroke="var(--color-green)" strokeWidth={1.8} dot={{ r: 2, fill: 'var(--color-green)' }} />
              </LineChart>
            </ResponsiveContainer>
          ) : <ChartEmpty message="No fuel data for this period" />}
        </ChartCard>

        <ChartCard title="Daily Trip Count" height={220}>
          {tripData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tripData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} minTickGap={40} />
                <YAxis tick={{ fontSize: 9, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} width={35} />
                <Tooltip content={<ChartTip />} />
                <Bar dataKey="count" name="Trips" fill="var(--color-blue)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <ChartEmpty message="No trips for this period" />}
        </ChartCard>
      </div>
    </div>
  );
});
