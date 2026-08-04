export function Spinner({ size = 'md', label = 'Loading…', className = '', ...props }) {
  const sizeClass = size === 'sm' ? ' ui-spinner--sm' : size === 'lg' ? ' ui-spinner--lg' : '';
  return (
    <div
      role="status"
      aria-label={label}
      className={`ui-spinner${sizeClass} ${className}`.trim()}
      {...props}
    />
  );
}
