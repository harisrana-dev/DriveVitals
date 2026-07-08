import { TrendingUp, TrendingDown } from 'lucide-react';
import Card from '../../../components/common/Card/Card';

const STATUS_TOKEN = {
  healthy: 'var(--color-status-healthy)',
  warning: 'var(--color-status-warning)',
  critical: 'var(--color-status-critical)',
  info: 'var(--color-status-info)',
  maintenance: 'var(--color-status-maintenance)',
  offline: 'var(--color-status-offline)',
};

// KPICard: Icon / Title / Primary metric / Trend / Context label
function KPICard({ icon: Icon, title, value, trend, trendDirection, context, status }) {
  const accent = STATUS_TOKEN[status] || STATUS_TOKEN.info;
  const TrendIcon = trendDirection === 'up' ? TrendingUp : TrendingDown;

  return (
    <Card className="kpi-card">
      <div className="kpi-card-top">
        <div className="kpi-card-icon" style={{ color: accent, backgroundColor: `${accent}1F` }}>
          <Icon size={18} strokeWidth={2} />
        </div>
        <span className="kpi-card-title text-caption">{title}</span>
      </div>

      <div className="kpi-card-value text-kpi-value">{value}</div>

      <div className="kpi-card-bottom">
        <span
          className={`kpi-card-trend kpi-card-trend--${trendDirection === 'up' ? 'up' : 'down'}`}
        >
          <TrendIcon size={13} strokeWidth={2.5} />
          {trend}
        </span>
        <span className="kpi-card-context text-caption">{context}</span>
      </div>
    </Card>
  );
}

export default KPICard;
