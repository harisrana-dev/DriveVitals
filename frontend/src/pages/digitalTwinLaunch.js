/**
 * Launch-target selection for the Digital Twin Lab Overview tab.
 *
 * Exactly one Ready scenario is an unambiguous target. Multiple Ready
 * scenarios are reported as a conflict so the UI can ask the operator to
 * choose on the Scenarios tab instead of silently substituting whichever
 * scenario happens to sort first (M5.1 regression guard).
 */
export function pickLaunchTarget(scenarios) {
  const ready = (scenarios || []).filter((s) => s?.status === 'ready');
  if (ready.length === 1) return { target: ready[0], conflict: [] };
  if (ready.length > 1) return { target: null, conflict: ready.map((s) => s.name) };
  return { target: null, conflict: [] };
}

export default pickLaunchTarget;
