import { describe, it, expect } from 'vitest';
import {
  SIDEBAR_WIDTH,
  SIDEBAR_COLLAPSED_WIDTH,
  SIDEBAR_MOBILE_WIDTH,
  SIDEBAR_MOBILE_BREAKPOINT,
  isSidebarMobileWidth,
  getMainContentMargin,
} from './sidebarLayout';

describe('getMainContentMargin', () => {
  it('uses the full sidebar width when expanded', () => {
    expect(getMainContentMargin(false)).toBe(SIDEBAR_WIDTH);
  });

  it('uses the collapsed width when collapsed', () => {
    expect(getMainContentMargin(true)).toBe(SIDEBAR_COLLAPSED_WIDTH);
  });

  it('always matches the desktop sidebar width so content never overlaps', () => {
    expect(getMainContentMargin(false)).toBe(SIDEBAR_WIDTH);
    expect(getMainContentMargin(true)).toBe(SIDEBAR_COLLAPSED_WIDTH);
    expect(SIDEBAR_COLLAPSED_WIDTH).toBeLessThan(SIDEBAR_WIDTH);
  });
});

describe('isSidebarMobileWidth', () => {
  it('returns true at or below the breakpoint', () => {
    expect(isSidebarMobileWidth(SIDEBAR_MOBILE_BREAKPOINT)).toBe(true);
    expect(isSidebarMobileWidth(800)).toBe(true);
  });

  it('returns false above the breakpoint', () => {
    expect(isSidebarMobileWidth(1280)).toBe(false);
  });
});

describe('sidebar width constants', () => {
  it('mobile sidebar is wider than the desktop sidebar', () => {
    expect(SIDEBAR_MOBILE_WIDTH).toBeGreaterThan(SIDEBAR_WIDTH);
  });
});