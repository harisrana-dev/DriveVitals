import './Card.css';

/**
 * Card
 * Base enterprise card container used across the dashboard.
 * Keep this component "dumb" — it only provides shell/chrome.
 *
 * Props:
 *  - title: optional string, rendered as card header title
 *  - action: optional node, rendered top-right of header (e.g. a link/icon)
 *  - noPadding: boolean, removes body padding (useful for tables)
 *  - className: extra classes for the outer card
 *  - children: card body content
 */
function Card({ title, action, noPadding = false, className = '', children }) {
  return (
    <div className={`card ${className}`}>
      {(title || action) && (
        <div className="card-header">
          {title && <h3 className="card-title text-card-title">{title}</h3>}
          {action && <div className="card-header-action">{action}</div>}
        </div>
      )}
      <div className={noPadding ? 'card-body card-body--no-padding' : 'card-body'}>
        {children}
      </div>
    </div>
  );
}

export default Card;
