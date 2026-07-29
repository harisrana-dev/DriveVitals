export function computeComponentHealth(v) {
  let engine = 100;
  if (v.coolantTemp > 105) engine -= 30;
  else if (v.coolantTemp > 95) engine -= 15;
  if (v.engineLoad > 85) engine -= 10;

  let braking = 100;
  if (v.harshBraking) braking -= 25;
  if (v.brakePressure > 0.7) braking -= 10;

  let fuel = 100;
  if (v.fuelLevel < 15) fuel -= 30;
  else if (v.fuelLevel < 30) fuel -= 15;
  if (v.aggressiveThrottle) fuel -= 20;

  let behaviour = 100;
  if (v.speeding) behaviour -= 15;
  if (v.aggressiveThrottle) behaviour -= 10;
  if (v.highRpm) behaviour -= 10;

  return {
    engine: Math.max(0, Math.min(100, engine)),
    braking: Math.max(0, Math.min(100, braking)),
    fuel: Math.max(0, Math.min(100, fuel)),
    behaviour: Math.max(0, Math.min(100, behaviour)),
  };
}

export function healthCategory(score) {
  if (score == null) return 'healthy';
  if (score >= 80) return 'healthy';
  if (score >= 50) return 'warning';
  return 'critical';
}

export function healthColor(category) {
  switch (category) {
    case 'healthy': return 'var(--color-green)';
    case 'warning': return 'var(--color-amber)';
    case 'critical': return 'var(--color-red)';
    default: return 'var(--color-text-muted)';
  }
}

export function healthBg(category) {
  switch (category) {
    case 'healthy': return 'var(--color-green-bg)';
    case 'warning': return 'var(--color-amber-bg)';
    case 'critical': return 'var(--color-red-bg)';
    default: return 'var(--color-bg)';
  }
}

export function componentLabel(key) {
  switch (key) {
    case 'engine': return 'Engine';
    case 'braking': return 'Braking';
    case 'fuel': return 'Fuel Efficiency';
    case 'behaviour': return 'Driver Behaviour';
    default: return key;
  }
}

export function componentIcon(key) {
  switch (key) {
    case 'engine': return '\u26ED';
    case 'braking': return '\u26FD';
    case 'fuel': return '\u26FD';
    case 'behaviour': return '\u26A0';
    default: return '\u25CF';
  }
}
