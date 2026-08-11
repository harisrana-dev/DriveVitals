export const HEALTHY_MIN = 90;
export const WARNING_MIN = 70;

export function canonicalHealthCategory(score, status) {
  if (status === 'healthy' || status === 'warning' || status === 'critical') {
    return status;
  }
  if (score == null) return 'unavailable';
  if (score >= HEALTHY_MIN) return 'healthy';
  if (score >= WARNING_MIN) return 'warning';
  return 'critical';
}

export function healthCategory(score) {
  return canonicalHealthCategory(score, null);
}

export function healthLabel(category) {
  switch (category) {
    case 'healthy': return 'Healthy';
    case 'warning': return 'Warning';
    case 'critical': return 'Critical';
    case 'unavailable': return 'Unavailable';
    default: return category || 'Unavailable';
  }
}

export function healthColor(categoryOrScore) {
  const category =
    typeof categoryOrScore === 'number' || categoryOrScore == null
      ? canonicalHealthCategory(categoryOrScore, null)
      : categoryOrScore;
  switch (category) {
    case 'healthy': return 'var(--color-green)';
    case 'warning': return 'var(--color-amber)';
    case 'critical': return 'var(--color-red)';
    default: return 'var(--color-text-muted)';
  }
}

export function healthBg(categoryOrScore) {
  const category =
    typeof categoryOrScore === 'number' || categoryOrScore == null
      ? canonicalHealthCategory(categoryOrScore, null)
      : categoryOrScore;
  switch (category) {
    case 'healthy': return 'var(--color-green-bg)';
    case 'warning': return 'var(--color-amber-bg)';
    case 'critical': return 'var(--color-red-bg)';
    default: return 'var(--color-surface-hover)';
  }
}

export function componentLabel(key) {
  switch (key) {
    case 'engine': return 'Engine';
    case 'cooling': return 'Cooling';
    case 'braking': return 'Brakes';
    case 'transmission': return 'Transmission';
    case 'fuel': return 'Fuel System';
    default: return key;
  }
}

export function healthReasonLabel(reason) {
  if (!reason) return 'Health concern detected';
  const idx = String(reason).indexOf(' (');
  const head = idx >= 0 ? String(reason).slice(0, idx) : String(reason);
  const detail = idx >= 0 ? String(reason).slice(idx) : '';
  return head.charAt(0).toUpperCase() + head.slice(1) + detail;
}
