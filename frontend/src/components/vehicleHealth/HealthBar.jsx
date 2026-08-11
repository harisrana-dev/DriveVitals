import { memo } from 'react';
import { canonicalHealthCategory, healthColor, healthLabel } from '../../utils/health';

export const HealthBar = memo(function HealthBar({ score, status, height, showLabel }) {
  const cat = canonicalHealthCategory(score ?? null, status ?? null);
  const color = healthColor(cat);
  const hasScore = score != null;

  return (
    <div style={{ width: '100%' }}>
      <div
        style={{
          width: '100%',
          height: height ?? 6,
          borderRadius: 3,
          background: 'var(--color-border-light)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${hasScore ? Math.max(0, Math.min(100, score)) : 0}%`,
            height: '100%',
            borderRadius: 3,
            background: hasScore ? color : 'var(--color-border)',
            transition: 'background-color 0.4s ease, width 0.4s ease',
          }}
        />
      </div>
      {showLabel && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: 4,
            fontSize: 11,
          }}
        >
          <span style={{ color: 'var(--color-text-secondary)', fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>
            {hasScore ? `${Math.round(score)}%` : '\u2014'}
          </span>
          <span style={{ color, fontWeight: 500, textTransform: 'capitalize' }}>{healthLabel(cat)}</span>
        </div>
      )}
    </div>
  );
});
