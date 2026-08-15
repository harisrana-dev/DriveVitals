import { memo, useState } from 'react';
import { BarChart3 } from 'lucide-react';

const CATEGORY_COLORS = {
  'Safety & Driving': 'var(--color-red)',
  'Vehicle Health': 'var(--color-purple)',
  Cooling: 'var(--color-blue)',
  Fuel: 'var(--color-green)',
  Engine: 'var(--color-amber)',
  Electrical: 'var(--color-accent)',
  Transmission: 'var(--color-text-muted)',
  Brakes: 'var(--color-red)',
  Maintenance: 'var(--color-amber)',
  Trip: 'var(--color-blue)',
  Other: 'var(--color-text-muted)',
  Unclassified: 'var(--color-text-muted)',
};

const SEVERITY_COLORS = {
  Critical: 'var(--color-red)',
  High: 'var(--color-amber)',
  Medium: 'var(--color-blue)',
  Low: 'var(--color-accent)',
  Information: 'var(--color-text-muted)',
};

const toggleBtn = {
  padding: '3px 8px',
  borderRadius: 6,
  fontSize: 10,
  fontWeight: 600,
  border: '1px solid var(--color-border)',
  background: 'transparent',
  color: 'var(--color-text-muted)',
  cursor: 'pointer',
  fontFamily: 'inherit',
  lineHeight: 1,
  transition: 'all 0.12s ease',
};

const toggleActive = {
  background: 'var(--color-accent-subtle)',
  color: 'var(--color-accent)',
  borderColor: 'var(--color-accent)',
};

/**
 * Distribution over ACTIVE alerts only. The population is disclosed under
 * the title ("of N active alerts"); null categories render as
 * "Unclassified" and never as "Other". Category bars are clickable and
 * drive the history table filter.
 */
export const AlertDistribution = memo(function AlertDistribution({
  categoryDist,
  severityDist,
  activeTotal,
  activeCategory,
  onCategorySelect,
}) {
  const [mode, setMode] = useState('category');
  const data = mode === 'category' ? categoryDist : severityDist;
  const maxCount = Math.max(...data.map((d) => d.count), 1);
  const colors = mode === 'category' ? CATEGORY_COLORS : SEVERITY_COLORS;

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
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
        <BarChart3 size={14} style={{ color: 'var(--color-accent)' }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
          Alert Distribution
        </span>
        <span style={{ display: 'flex', gap: 4, marginLeft: 'auto' }}>
          <button
            onClick={() => setMode('category')}
            style={{ ...toggleBtn, ...(mode === 'category' ? toggleActive : {}) }}
          >
            Category
          </button>
          <button
            onClick={() => setMode('severity')}
            style={{ ...toggleBtn, ...(mode === 'severity' ? toggleActive : {}) }}
          >
            Severity
          </button>
        </span>
      </div>
      <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 12 }}>
        {mode === 'category' ? 'Active alerts by category' : 'Active alerts by severity'} · of {activeTotal} active {activeTotal === 1 ? 'alert' : 'alerts'}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {data.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            No active alerts.
          </div>
        ) : (
          data.map((item) => {
            const color = colors[item.label] || 'var(--color-text-muted)';
            const widthPct = (item.count / maxCount) * 100;
            const isCatMode = mode === 'category' && onCategorySelect;
            const selected = isCatMode && (item.key ?? '__unclassified__') === activeCategory;
            const rowStyle = {
              display: 'flex',
              flexDirection: 'column',
              gap: 3,
              borderRadius: 8,
              padding: isCatMode ? '4px 6px' : 0,
              cursor: isCatMode ? 'pointer' : 'default',
              background: selected ? 'var(--color-accent-subtle)' : 'transparent',
            };
            return (
              <div
                key={`${mode}-${item.key ?? item.label}`}
                onClick={() => isCatMode && onCategorySelect(item.key ?? '__unclassified__')}
                style={rowStyle}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                  <span style={{ color: selected ? 'var(--color-accent)' : 'var(--color-text-secondary)', fontWeight: 500 }}>
                    {item.label}
                  </span>
                  <span style={{ color: 'var(--color-text-primary)', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                    {item.count} · {item.pct}%
                  </span>
                </div>
                <div
                  style={{
                    width: '100%',
                    height: 8,
                    borderRadius: 4,
                    background: 'var(--color-border-light)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${widthPct}%`,
                      height: '100%',
                      borderRadius: 4,
                      background: color,
                      transition: 'width 0.5s ease, background-color 0.3s ease',
                    }}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
});
