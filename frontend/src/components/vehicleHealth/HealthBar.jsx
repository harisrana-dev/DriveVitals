import { memo } from 'react';
import { healthCategory, healthColor } from '../../utils/health';

export const HealthBar = memo(function HealthBar({ score, height, showLabel }) {
  const cat = healthCategory(score);
  const color = healthColor(cat);

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
            width: `${Math.max(0, Math.min(100, score ?? 0))}%`,
            height: '100%',
            borderRadius: 3,
            background: color,
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
            {Math.round(score ?? 0)}%
          </span>
          <span style={{ color, fontWeight: 500, textTransform: 'capitalize' }}>{cat}</span>
        </div>
      )}
    </div>
  );
});
