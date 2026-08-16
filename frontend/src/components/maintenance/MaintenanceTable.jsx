import { memo } from 'react';
import { ChevronsUpDown, ArrowUpRight } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { PriorityBadge } from './PriorityBadge';
import { formatMaintenanceDue, sortMaintenanceWorkItems } from '../../utils/maintenance';

const GRID = '1.3fr 1fr 1.35fr 0.9fr 1.1fr 0.7fr 96px';

const SORT_OPTIONS = [
  { key: 'status', label: 'Status' },
  { key: 'priority', label: 'Priority' },
  { key: 'remaining', label: 'Due (km)' },
  { key: 'vehicle', label: 'Vehicle' },
];

export const MaintenanceTable = memo(function MaintenanceTable({
  workItems,
  onOpenVehicle,
  sortBy,
  onSortChange,
}) {
  const list = sortMaintenanceWorkItems(workItems, sortBy);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 6, marginBottom: 8 }}>
        <ChevronsUpDown size={12} style={{ color: 'var(--color-text-muted)' }} />
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Sort</span>
        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value)}
          style={{
            padding: '3px 8px',
            borderRadius: 6,
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-primary)',
            fontSize: 11,
            fontFamily: 'inherit',
            cursor: 'pointer',
          }}
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.key} value={o.key}>{o.label}</option>
          ))}
        </select>
      </div>

      <div style={{ border: '1px solid var(--color-border)', borderRadius: 10, overflow: 'hidden' }}>
        <div style={{ maxHeight: 460, overflowY: 'auto', scrollbarGutter: 'stable' }}>
          <div
            style={{
              position: 'sticky',
              top: 0,
              zIndex: 2,
              display: 'grid',
              gridTemplateColumns: GRID,
              gap: 10,
              padding: '10px 12px 8px',
              fontSize: 10,
              fontWeight: 600,
              color: 'var(--color-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              background: 'var(--color-surface)',
              borderBottom: '1px solid var(--color-border)',
            }}
          >
            <span>Vehicle</span>
            <span>Driver</span>
            <span>Service</span>
            <span>Status</span>
            <span>Due</span>
            <span>Priority</span>
            <span style={{ textAlign: 'right' }}>Action</span>
          </div>

          {list.length === 0 ? (
            <div style={{ padding: '28px 16px', textAlign: 'center', fontSize: 12, color: 'var(--color-text-muted)' }}>
              No work items match the current filters.
            </div>
          ) : (
            list.map((item) => (
              <WorkRow
                key={item.workKey}
                item={item}
                onClick={() => onOpenVehicle && onOpenVehicle(item.vehicle_id)}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
});

function WorkRow({ item, onClick }) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && onClick) {
          e.preventDefault();
          onClick();
        }
      }}
      style={{
        display: 'grid',
        gridTemplateColumns: GRID,
        gap: 10,
        alignItems: 'center',
        padding: '9px 12px',
        borderBottom: '1px solid var(--color-border-light)',
        background: 'transparent',
        cursor: 'pointer',
        transition: 'background-color 0.12s ease',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-hover)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {item.vehicle_name}
      </span>

      <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {item.driver_name || '\u2014'}
      </span>

      <span style={{ minWidth: 0 }}>
        <span
          style={{
            display: 'block',
            fontSize: 12,
            fontWeight: 500,
            color: 'var(--color-text-primary)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {item.maintenanceTypeLabel}
        </span>
        <span style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>
          {item.component || '\u2014'}
          {item.projectionCount > 1 ? ` · ${item.projectionCount} projections` : ''}
        </span>
      </span>

      <span><StatusBadge status={item.dueStatus} size="sm" /></span>

      <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {formatMaintenanceDue(item)}
      </span>

      <span><PriorityBadge priority={item.priority} size="sm" /></span>

      <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
        <button
          onClick={(e) => { e.stopPropagation(); if (onClick) onClick(); }}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 3,
            padding: '4px 8px',
            borderRadius: 6,
            border: '1px solid var(--color-border)',
            background: 'transparent',
            color: 'var(--color-text-secondary)',
            fontSize: 10,
            fontWeight: 600,
            cursor: 'pointer',
            fontFamily: 'inherit',
            lineHeight: 1,
            transition: 'all 0.12s ease',
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
          Open
          <ArrowUpRight size={11} />
        </button>
      </span>
    </div>
  );
}
