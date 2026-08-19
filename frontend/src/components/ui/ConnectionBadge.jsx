const STATUS_META = {
  live: { label: 'LIVE', color: 'var(--color-green)' },
  stale: { label: 'STALE', color: 'var(--color-amber)' },
  connecting: { label: 'CONNECTING', color: 'var(--color-amber)' },
  offline: { label: 'OFFLINE', color: 'var(--color-red)' },
  syncing: { label: 'SYNCING', color: 'var(--color-blue)' },
};

export function ConnectionBadge({ status }) {
  const meta = STATUS_META[status] || STATUS_META.offline;

  return (
    <div
      title="Data connection status"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        padding: '5px 10px',
        borderRadius: 8,
        border: '1px solid var(--color-border)',
        background: 'var(--color-surface)',
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: '0.5px',
        color: 'var(--color-text-secondary)',
        whiteSpace: 'nowrap',
      }}
    >
      <span style={{
        width: 8,
        height: 8,
        borderRadius: '50%',
        background: meta.color,
        boxShadow: `0 0 0 3px ${meta.color}33`,
      }} />
      {meta.label}
    </div>
  );
}
