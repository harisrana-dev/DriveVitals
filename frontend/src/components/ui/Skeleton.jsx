export function Skeleton({ className = '', style, ...props }) {
  return <div className={`ui-skeleton ${className}`.trim()} style={style} {...props} />;
}

export function SkeletonText({ width = '100%', className = '', style, ...props }) {
  return (
    <div
      className={`ui-skeleton ui-skeleton--text ${className}`.trim()}
      style={{ width, ...style }}
      {...props}
    />
  );
}

export function SkeletonCircle({ size = 32, className = '', style, ...props }) {
  return (
    <div
      className={`ui-skeleton ui-skeleton--circle ${className}`.trim()}
      style={{ width: size, height: size, ...style }}
      {...props}
    />
  );
}
