export function EmptyState({ title, description, icon, action, className = '', ...props }) {
  return (
    <div className={`ui-empty ${className}`.trim()} {...props}>
      {icon && <div className="ui-empty__icon">{icon}</div>}
      {title && <div className="ui-empty__title">{title}</div>}
      {description && <p className="ui-empty__description">{description}</p>}
      {action && <div className="ui-empty__action">{action}</div>}
    </div>
  );
}
