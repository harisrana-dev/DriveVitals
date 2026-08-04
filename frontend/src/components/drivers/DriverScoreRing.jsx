import { memo } from 'react';

function scoreColor(score) {
  if (score >= 90) return 'var(--color-green)';
  if (score >= 70) return 'var(--color-amber)';
  return 'var(--color-red)';
}

function scoreBg(score) {
  if (score >= 90) return 'var(--color-green-bg)';
  if (score >= 70) return 'var(--color-amber-bg)';
  return 'var(--color-red-bg)';
}

export const DriverScoreRing = memo(function DriverScoreRing({ score, size = 80, strokeWidth }) {
  const s = strokeWidth || Math.max(4, Math.round(size * 0.08));
  const r = (size - s) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  const color = scoreColor(score);
  const bg = scoreBg(score);

  return (
    <div
      style={{
        position: 'relative',
        width: size,
        height: size,
        flexShrink: 0,
      }}
    >
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={bg}
          strokeWidth={s}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={s}
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{
            transition: 'stroke-dashoffset 0.6s ease-out',
          }}
        />
      </svg>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <span
          style={{
            fontSize: size < 72 ? 14 : 18,
            fontWeight: 700,
            color,
            fontVariantNumeric: 'tabular-nums',
            lineHeight: 1,
          }}
        >
          {Math.round(score)}
        </span>
        <span
          style={{
            fontSize: 9,
            color: 'var(--color-text-muted)',
            lineHeight: 1,
            marginTop: 1,
          }}
        >
          /100
        </span>
      </div>
    </div>
  );
});
