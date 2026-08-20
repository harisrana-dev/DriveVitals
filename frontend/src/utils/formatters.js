/**
 * Canonical formatting utilities for DriveVitals.
 *
 * All display formatting for units, durations, and values flows through
 * here. Components MUST NOT define their own formatters for the same
 * concepts — this module is the single source of truth.
 */

const SECONDS_PER_MINUTE = 60;
const SECONDS_PER_HOUR = 3600;
const SECONDS_PER_DAY = 86400;
const SECONDS_PER_MONTH = 30 * SECONDS_PER_DAY;

/**
 * Format a duration in seconds to a human-readable string.
 *
 * Examples:
 *   null / 0   → "—"
 *   30         → "30s"
 *   120        → "2m"
 *   3720       → "1h 2m"
 *   93600      → "1d 2h"
 *   5184000    → "approximately 2 months"
 */
export function formatDuration(seconds) {
  if (seconds == null || seconds <= 0) return '\u2014';

  const totalSeconds = Math.round(seconds);

  if (totalSeconds < SECONDS_PER_MINUTE) {
    return `${totalSeconds}s`;
  }

  if (totalSeconds < SECONDS_PER_HOUR) {
    const mins = Math.floor(totalSeconds / SECONDS_PER_MINUTE);
    const secs = totalSeconds % SECONDS_PER_MINUTE;
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
  }

  if (totalSeconds < SECONDS_PER_DAY) {
    const hrs = Math.floor(totalSeconds / SECONDS_PER_HOUR);
    const mins = Math.floor((totalSeconds % SECONDS_PER_HOUR) / SECONDS_PER_MINUTE);
    return mins > 0 ? `${hrs}h ${mins}m` : `${hrs}h`;
  }

  if (totalSeconds < 3 * SECONDS_PER_MONTH) {
    const days = Math.floor(totalSeconds / SECONDS_PER_DAY);
    const hrs = Math.floor((totalSeconds % SECONDS_PER_DAY) / SECONDS_PER_HOUR);
    return hrs > 0 ? `${days}d ${hrs}h` : `${days}d`;
  }

  const months = Math.round(totalSeconds / SECONDS_PER_MONTH);
  return `approximately ${months} month${months === 1 ? '' : 's'}`;
}

/**
 * Format an alert's age based on its created_at timestamp.
 * Returns a human-readable duration string.
 */
export function formatAlertDuration(createdAt, now = Date.now()) {
  if (!createdAt) return '\u2014';
  const t = new Date(createdAt).getTime();
  if (Number.isNaN(t)) return '\u2014';
  const elapsed = (now - t) / 1000;
  return formatDuration(elapsed);
}

/**
 * Format a number to one decimal place, or return "—" for null/undefined.
 */
export function formatNumber(value, decimals = 1) {
  if (value == null || !Number.isFinite(Number(value))) return '\u2014';
  return Number(value).toFixed(decimals);
}

/**
 * Format a percentage with a space before the % sign.
 * Examples: 90 → "90 %", 72.5 → "72.5 %", null → "—"
 */
export function formatPercent(value, decimals = 0) {
  if (value == null || !Number.isFinite(Number(value))) return '\u2014';
  return `${Number(value).toFixed(decimals)} %`;
}

/**
 * Format fuel efficiency in km/L.
 * Examples: 15.4 → "15.4 km/L", null → "—"
 */
export function formatFuelEfficiency(kmPerL) {
  if (kmPerL == null || !Number.isFinite(Number(kmPerL))) return '\u2014';
  return `${Number(kmPerL).toFixed(1)} km/L`;
}

/**
 * Format a temperature in degrees Celsius with proper spacing.
 * Examples: 90 → "90 °C", 89.5 → "90 °C", null → "—"
 */
export function formatTemperature(value) {
  if (value == null || !Number.isFinite(Number(value))) return '\u2014';
  return `${Math.round(Number(value))} \u00B0C`;
}

/**
 * Format a temperature with one decimal place.
 */
export function formatTemperaturePrecise(value) {
  if (value == null || !Number.isFinite(Number(value))) return '\u2014';
  return `${Number(value).toFixed(1)} \u00B0C`;
}

/**
 * Format fuel consumed in litres.
 * Examples: 42.3 → "42.3 L", null → "—"
 */
export function formatFuelLiters(liters) {
  if (liters == null || !Number.isFinite(Number(liters))) return '\u2014';
  return `${Number(liters).toFixed(1)} L`;
}

/**
 * Format fuel level as percentage.
 * Examples: 64 → "64 %", null → "—"
 */
export function formatFuelLevel(percent) {
  if (percent == null || !Number.isFinite(Number(percent))) return '\u2014';
  return `${Math.round(percent)} %`;
}

/**
 * Format distance in km or m.
 * Examples: 12.5 → "12.5 km", 0.5 → "500 m", null → "—"
 */
export function formatDistance(km) {
  if (km == null || !Number.isFinite(Number(km)) || km <= 0) return '\u2014';
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(1)} km`;
}

/**
 * Format speed in km/h.
 */
export function formatSpeed(kmh) {
  if (kmh == null || !Number.isFinite(Number(kmh))) return '\u2014';
  return `${Math.round(kmh)} km/h`;
}

/**
 * Format an event rate per 100 km.
 */
export function formatEventRate(rate) {
  if (rate == null || !Number.isFinite(Number(rate))) return '\u2014';
  return `${Number(rate).toFixed(1)} / 100 km`;
}
