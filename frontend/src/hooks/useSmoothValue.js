import { useEffect, useRef, useState } from 'react';

export function useSmoothValue(value, duration = 400) {
  const prevValue = useRef(value);
  const [displayed, setDisplayed] = useState(value);
  const frameRef = useRef(null);
  const fromRef = useRef(value);

  useEffect(() => {
    const from = fromRef.current;
    const to = value;
    const diff = to - from;

    if (Math.abs(diff) < 0.3) {
      setDisplayed(to);
      fromRef.current = to;
      prevValue.current = to;
      return;
    }

    const start = performance.now();

    function animate(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayed(from + diff * eased);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      } else {
        fromRef.current = to;
        prevValue.current = to;
      }
    }

    frameRef.current = requestAnimationFrame(animate);
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [value, duration]);

  useEffect(() => {
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, []);

  return displayed;
}
