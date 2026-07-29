export function FuelBar({ level }) {
  const pct = Math.max(0, Math.min(100, level ?? 0));

  let color = 'var(--color-green)';
  if (pct < 15) color = 'var(--color-red)';
  else if (pct < 30) color = 'var(--color-amber)';

  return (
    <div style={{ width: '100%' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: 11,
          marginBottom: 4,
        }}
      >
        <span style={{ color: 'var(--color-text-muted)' }}>Fuel</span>
        <span style={{ color: 'var(--color-text-secondary)', fontWeight: 500 }}>
          {pct}%
        </span>
      </div>
      <div
        style={{
          width: '100%',
          height: 5,
          borderRadius: 3,
          background: 'var(--color-border-light)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            borderRadius: 3,
            background: color,
            transition: 'width 0.4s ease, background-color 0.3s ease',
          }}
        />
      </div>
    </div>
  );
}
