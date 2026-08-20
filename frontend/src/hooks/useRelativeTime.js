import { useEffect, useState } from 'react';

const SECONDS_PER_DAY = 86400;
const SECONDS_PER_MONTH = 30 * SECONDS_PER_DAY;

function compute(iso) {
  if (!iso) return '\u2014';
  const diff = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 3) return 'Just now';
  if (sec < 60) return `${sec} sec ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} min ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} hour${hr > 1 ? 's' : ''} ago`;
  const days = Math.floor(sec / SECONDS_PER_DAY);
  if (days < 4) return `${days} day${days > 1 ? 's' : ''} ago`;
  if (days < 30) return `${Math.floor(days / 7)} week${Math.floor(days / 7) > 1 ? 's' : ''} ago`;
  const months = Math.round(sec / SECONDS_PER_MONTH);
  return `${months} month${months > 1 ? 's' : ''} ago`;
}

export function useRelativeTime(iso) {
  const [text, setText] = useState(() => compute(iso));

  useEffect(() => {
    const id = setTimeout(() => setText(compute(iso)), 0);
    const interval = setInterval(() => {
      setText(compute(iso));
    }, 1000);
    return () => { clearTimeout(id); clearInterval(interval); };
  }, [iso]);

  return text;
}
