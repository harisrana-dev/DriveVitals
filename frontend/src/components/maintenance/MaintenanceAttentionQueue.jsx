import { memo } from 'react';
import { Wrench, ArrowUpRight } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { PriorityBadge } from './PriorityBadge';
import { formatMaintenanceDue, sortMaintenanceWorkItems } from '../../utils/maintenance';

/**
 * Attention queue: work items that are overdue or due soon, surfaced for
 * immediate response. Derived entirely from the canonical work items.
 */
export const MaintenanceAttentionQueue = memo(function MaintenanceAttentionQueue({
  workItems,
  onOpenVehicle,
}) {
  const list = sortMaintenanceWorkItems(
    (Array.isArray(workItems) ? workItems : []).filter(
      (w) => w.dueStatus === 'overdue' || w.dueStatus === 'dueSoon'
    ),
    'status'
  );

  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        padding: 20,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
        <Wrench size={14} style={{ color: 'var(--color-amber)' }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
          Attention Queue
        </span>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 4 }}>
          {list.length} open
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 320, overflowY: 'auto' }}>
        {list.length === 0 ? (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '8px 0' }}>
            No work items are overdue or due soon.
          </div>
        ) : (
          list.map((item) => (
            <QueueRow
              key={item.workKey}
              item={item}
              onClick={() => onOpenVehicle && onOpenVehicle(item.vehicle_id)}
            />
          ))
        )}
      </div>
    </div>
  );
});

function QueueRow({ item, onClick }) {
  const urgent = item.dueStatus === 'overdue';
  const color = urgent ? 'var(--color-red)' : 'var(--color-amber)';
  const bg = urgent ? 'var(--color-red-bg)' : 'var(--color-amber-bg)';

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
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '9px 12px',
        borderRadius: 8,
        background: bg,
        border: `1px solid ${color}`,
        cursor: 'pointer',
        transition: 'all 0.15s ease',
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
          <span
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {item.vehicle_name}
          </span>
          <StatusBadge status={item.dueStatus} size="sm" />
          <PriorityBadge priority={item.priority} size="sm" />
        </div>
        <div
          style={{
            fontSize: 11,
            color: 'var(--color-text-secondary)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {item.maintenanceTypeLabel}
          {item.projectionCount > 1 ? ` · ${item.projectionCount} projections` : ''}
          {item.driver_name ? ` · ${item.driver_name}` : ''}
        </div>
      </div>

      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-primary)', fontVariantNumeric: 'tabular-nums' }}>
          {formatMaintenanceDue(item)}
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); if (onClick) onClick(); }}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 3,
            marginTop: 3,
            padding: '3px 8px',
            borderRadius: 6,
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-secondary)',
            fontSize: 10,
            fontWeight: 600,
            cursor: 'pointer',
            fontFamily: 'inherit',
            lineHeight: 1,
            transition: 'all 0.12s ease',
          }}
        >
          Open
          <ArrowUpRight size={11} />
        </button>
      </div>
    </div>
  );
}
