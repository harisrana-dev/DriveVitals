import { useEffect, useState } from 'react';

function compute(iso) {
  if (!iso) return 'Just now';
  const diff = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 3) return 'Just now';
  if (sec < 60) return `${sec} sec ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} min ago`;
  const hr = Math.floor(min / 60);
  return `${hr} hour${hr > 1 ? 's' : ''} ago`;
}

export function useRelativeTime(iso) {
  const [text, setText] = useState(() => compute(iso));

  useEffect(() => {
    setText(compute(iso));
    const interval = setInterval(() => {
      setText(compute(iso));
    }, 1000);
    return () => clearInterval(interval);
  }, [iso]);

  return text;
}
