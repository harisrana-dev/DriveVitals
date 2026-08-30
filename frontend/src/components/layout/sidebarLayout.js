export const SIDEBAR_WIDTH = 240;
export const SIDEBAR_COLLAPSED_WIDTH = 64;
export const SIDEBAR_MOBILE_WIDTH = 260;
export const SIDEBAR_MOBILE_BREAKPOINT = 1024;

export function isSidebarMobileWidth(width) {
  return width <= SIDEBAR_MOBILE_BREAKPOINT;
}

export function getMainContentMargin(collapsed) {
  return collapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH;
}