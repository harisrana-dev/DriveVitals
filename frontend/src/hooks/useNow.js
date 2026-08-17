import { useEffect, useState } from 'react';

/**
 * Re-renders on a fixed cadence with the current timestamp. Used to keep
 * connection-state / relative-time derived values fresh without each
 * consumer wiring its own interval.
 */
export function useNow(intervalMs = 1000) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  return now;
}
