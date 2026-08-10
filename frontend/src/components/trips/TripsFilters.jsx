import { memo } from 'react';
import { Search, ArrowUpDown, RotateCcw } from 'lucide-react';

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'aborted', label: 'Aborted' },
];

const routeTypeOptions = [
  { value: '', label: 'All Routes' },
  { value: 'urban', label: 'Urban' },
  { value: 'highway', label: 'Highway' },
  { value: 'rural', label: 'Rural' },
];

const gradeOptions = [
  { value: '', label: 'All Grades' },
  { value: 'A', label: 'Grade A' },
  { value: 'B', label: 'Grade B' },
  { value: 'C', label: 'Grade C' },
  { value: 'D', label: 'Grade D' },
  { value: 'F', label: 'Grade F' },
];

const sortOptions = [
  { value: 'date', label: 'Date' },
  { value: 'distance', label: 'Distance' },
  { value: 'score', label: 'Safety Score' },
  { value: 'fuel', label: 'Fuel Used' },
];

const selectStyle = {
  padding: '8px 12px',
  borderRadius: 8,
  border: '1px solid var(--color-border)',
  background: 'var(--color-surface)',
  color: 'var(--color-text-primary)',
  fontSize: 13,
  outline: 'none',
  cursor: 'pointer',
  minWidth: 120,
  transition: 'border-color 0.15s ease',
};

export const TripsFilters = memo(function TripsFilters({
  search,
  onSearchChange,
  statusFilter,
  onStatusChange,
  routeFilter,
  onRouteChange,
  driverFilter,
  onDriverChange,
  driverOptions = [],
  vehicleFilter,
  onVehicleChange,
  vehicleOptions = [],
  gradeFilter,
  onGradeChange,
  dateFrom,
  onDateFromChange,
  dateTo,
  onDateToChange,
  onReset,
  sortBy,
  onSortChange,
  sortAsc,
  onSortToggle,
}) {
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
          flex: '1 1 200px',
          minWidth: 160,
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
          placeholder="Search trips, vehicles, drivers, routes..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          style={{
            width: '100%',
            padding: '8px 12px 8px 34px',
            borderRadius: 8,
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-primary)',
            fontSize: 13,
            outline: 'none',
            transition: 'border-color 0.15s ease',
          }}
          onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-accent)'; }}
          onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
        />
      </div>

      <select
        value={statusFilter}
        onChange={(e) => onStatusChange(e.target.value)}
        style={selectStyle}
      >
        {statusOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      <select
        value={routeFilter}
        onChange={(e) => onRouteChange(e.target.value)}
        style={selectStyle}
      >
        {routeTypeOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      <select
        value={driverFilter}
        onChange={(e) => onDriverChange(e.target.value)}
        style={selectStyle}
      >
        <option value="">All Drivers</option>
        {driverOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      <select
        value={vehicleFilter}
        onChange={(e) => onVehicleChange(e.target.value)}
        style={selectStyle}
      >
        <option value="">All Vehicles</option>
        {vehicleOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      <select
        value={gradeFilter}
        onChange={(e) => onGradeChange(e.target.value)}
        style={selectStyle}
      >
        {gradeOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => onDateFromChange(e.target.value)}
          aria-label="From date"
          style={{
            padding: '7px 10px',
            borderRadius: 8,
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-primary)',
            fontSize: 13,
            outline: 'none',
            fontFamily: 'inherit',
          }}
        />
        <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>→</span>
        <input
          type="date"
          value={dateTo}
          onChange={(e) => onDateToChange(e.target.value)}
          aria-label="To date"
          style={{
            padding: '7px 10px',
            borderRadius: 8,
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-primary)',
            fontSize: 13,
            outline: 'none',
            fontFamily: 'inherit',
          }}
        />
      </div>

      {(search || statusFilter || routeFilter || driverFilter || vehicleFilter || gradeFilter || dateFrom || dateTo) && (
        <button
          onClick={onReset}
          title="Clear all filters"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            padding: '8px 10px',
            borderRadius: 8,
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-secondary)',
            fontSize: 12,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-surface-hover)';
            e.currentTarget.style.color = 'var(--color-text-primary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--color-surface)';
            e.currentTarget.style.color = 'var(--color-text-secondary)';
          }}
        >
          <RotateCcw size={13} />
          Reset
        </button>
      )}

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 4,
          marginLeft: 'auto',
        }}
      >
        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value)}
          style={{
            ...selectStyle,
            borderRadius: '8px 0 0 8px',
            borderRight: 'none',
            minWidth: 90,
          }}
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
            padding: '8px 10px',
            borderRadius: '0 8px 8px 0',
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-surface-hover)';
            e.currentTarget.style.color = 'var(--color-text-primary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--color-surface)';
            e.currentTarget.style.color = 'var(--color-text-secondary)';
          }}
        >
          <ArrowUpDown size={14} strokeWidth={1.8} />
        </button>
      </div>
    </div>
  );
});
