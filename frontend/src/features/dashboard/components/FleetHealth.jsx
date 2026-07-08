import Card from '../../../components/common/Card/Card';

// FleetHealth: fleet-wide status breakdown strip.
// Sprint 1 restriction: no gauges, no charts — plain counts + status badges only.
const STATUS_BREAKDOWN = [
  { key: 'healthy', label: 'Healthy', count: 32, color: 'var(--color-status-healthy)' },
  { key: 'warning', label: 'Warning', count: 9, color: 'var(--color-status-warning)' },
  { key: 'critical', label: 'Critical', count: 4, color: 'var(--color-status-critical)' },
  { key: 'maintenance', label: 'In Maintenance', count: 3, color: 'var(--color-status-maintenance)' },
  { key: 'offline', label: 'Offline', count: 6, color: 'var(--color-status-offline)' },
];

function FleetHealth() {
  return (
    <Card title="Fleet Health Overview" className="fleet-health">
      <div className="fleet-health-breakdown">
        {STATUS_BREAKDOWN.map(({ key, label, count, color }) => (
          <div key={key} className="fleet-health-item">
            <span className="fleet-health-dot" style={{ backgroundColor: color }} />
            <span className="fleet-health-count">{count}</span>
            <span className="fleet-health-label text-caption">{label}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

export default FleetHealth;
