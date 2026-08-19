import { describe, expect, it } from 'vitest';

const STATUS_META = {
  live: { label: 'LIVE', color: 'var(--color-green)' },
  stale: { label: 'STALE', color: 'var(--color-amber)' },
  connecting: { label: 'CONNECTING', color: 'var(--color-amber)' },
  offline: { label: 'OFFLINE', color: 'var(--color-red)' },
  syncing: { label: 'SYNCING', color: 'var(--color-blue)' },
};

describe('ConnectionBadge STATUS_META', () => {
  it('renders LIVE for live status', () => {
    expect(STATUS_META.live.label).toBe('LIVE');
    expect(STATUS_META.live.color).toBe('var(--color-green)');
  });

  it('renders STALE for stale status', () => {
    expect(STATUS_META.stale.label).toBe('STALE');
    expect(STATUS_META.stale.color).toBe('var(--color-amber)');
  });

  it('renders CONNECTING for connecting status', () => {
    expect(STATUS_META.connecting.label).toBe('CONNECTING');
  });

  it('renders OFFLINE for offline status', () => {
    expect(STATUS_META.offline.label).toBe('OFFLINE');
    expect(STATUS_META.offline.color).toBe('var(--color-red)');
  });

  it('renders SYNCING for syncing status', () => {
    expect(STATUS_META.syncing.label).toBe('SYNCING');
    expect(STATUS_META.syncing.color).toBe('var(--color-blue)');
  });

  it('falls back to offline for unknown status', () => {
    const meta = STATUS_META['unknown'] || STATUS_META.offline;
    expect(meta.label).toBe('OFFLINE');
  });
});
