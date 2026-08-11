import { memo } from 'react';
import { Search, ArrowUpDown, RotateCcw } from 'lucide-react';

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'healthy', label: 'Healthy' },
  { value: 'warning', label: 'Warning' },
  { value: 'critical', label: 'Critical' },
  { value: 'unavailable', label: 'Unavailable' },
];

const sortOptions = [
  { value: 'name', label: 'Name' },
  { value: 'overallHealth', label: 'Health Score' },
  { value: 'speed', label: 'Speed' },
  { value: 'rpm', label: 'RPM' },
];

const inputBase = {
  padding: '8px 12px',
  borderRadius: 8,
  border: '1px solid var(--color-border)',
  background: 'var(--color-surface)',
  color: 'var(--color-text-primary)',
  fontSize: 13,
  outline: 'none',
  cursor: 'pointer',
  transition: 'border-color 0.15s ease',
};

export const HealthFilters = memo(function HealthFilters({
  search,
  onSearchChange,
  statusFilter,
  onStatusChange,
  minScore,
  onMinScoreChange,
  maxScore,
  onMaxScoreChange,
  sortBy,
  onSortChange,
  sortAsc,
  onSortToggle,
  hasActiveFilters,
  onReset,
}) {
  const handleFocus = (e) => { e.currentTarget.style.borderColor = 'var(--color-accent)'; };
  const handleBlur = (e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        flexWrap: 'wrap',
      }}
    >
      <div
        style={{
          position: 'relative',
          flex: '1 1 220px',
          minWidth: 180,
        }}
      >
        <Search
          size={14}
          style={{
            position: 'absolute',
            left: 12,
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--color-text-muted)',
            pointerEvents: 'none',
          }}
        />
        <input
          type="text"
          placeholder="Search vehicles..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          style={{
            ...inputBase,
            width: '100%',
            paddingLeft: 34,
            cursor: 'text',
          }}
          onFocus={handleFocus}
          onBlur={handleBlur}
        />
      </div>

      <select
        value={statusFilter}
        onChange={(e) => onStatusChange(e.target.value)}
        style={{ ...inputBase, minWidth: 130 }}
        onFocus={handleFocus}
        onBlur={handleBlur}
      >
        {statusOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 4,
        }}
      >
        <input
          type="number"
          min={0}
          max={100}
          placeholder="Min"
          value={minScore}
          onChange={(e) => onMinScoreChange(e.target.value)}
          aria-label="Minimum health score"
          style={{ ...inputBase, width: 64, cursor: 'text' }}
          onFocus={handleFocus}
          onBlur={handleBlur}
        />
        <span style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>to</span>
        <input
          type="number"
          min={0}
          max={100}
          placeholder="Max"
          value={maxScore}
          onChange={(e) => onMaxScoreChange(e.target.value)}
          aria-label="Maximum health score"
          style={{ ...inputBase, width: 64, cursor: 'text' }}
          onFocus={handleFocus}
          onBlur={handleBlur}
        />
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 4,
        }}
      >
        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value)}
          style={{ ...inputBase, borderRadius: '8px 0 0 8px', borderRight: 'none', minWidth: 110 }}
          onFocus={handleFocus}
          onBlur={handleBlur}
        >
          {sortOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              Sort: {opt.label}
            </option>
          ))}
        </select>
        <button
          onClick={onSortToggle}
          aria-label={`Sort ${sortAsc ? 'descending' : 'ascending'}`}
          style={{
            ...inputBase,
            borderRadius: '0 8px 8px 0',
            display: 'flex',
            alignItems: 'center',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--color-surface)'; }}
        >
          <ArrowUpDown size={14} strokeWidth={1.8} />
        </button>
      </div>

      {hasActiveFilters && (
        <button
          onClick={onReset}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '8px 12px',
            borderRadius: 8,
            border: '1px solid var(--color-border)',
            background: 'transparent',
            color: 'var(--color-text-secondary)',
            fontSize: 13,
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-surface-hover)';
            e.currentTarget.style.color = 'var(--color-text-primary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = 'var(--color-text-secondary)';
          }}
        >
          <RotateCcw size={13} />
          Reset
        </button>
      )}
    </div>
  );
});
