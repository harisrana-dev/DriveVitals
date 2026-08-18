/**
 * Drawer composition utilities.
 *
 * When a child drawer (e.g. Maintenance) opens from within a parent
 * drawer (e.g. Vehicle), the parent should shift left and the child
 * should open beside it at a higher z-index. This module provides the
 * layout logic so all drawers compose correctly.
 */

/**
 * Compute the stacking offset for a drawer based on its depth.
 * Each nested level shifts right by the width of the previous drawer
 * plus a small gap.
 */
export function drawerStackOffset(depth, parentWidth = 440) {
  if (depth <= 0) return 0;
  return parentWidth + 16;
}

/**
 * Compute the z-index for a drawer based on its depth.
 * Base drawer is z-301, each level adds 10.
 */
export function drawerZIndex(depth) {
  return 301 + depth * 10;
}

/**
 * Overlay z-index (always one below the drawer it overlays).
 */
export function overlayZIndex(depth) {
  return 300 + depth * 10;
}
