import Card from '../../../components/common/Card/Card';

/* ── Colour tokens per spec ──────────────────────────────────
   🟢 healthy   = #22c55e  (Active / All Clear)
   🔵 info      = #3b82f6  (Analytics / Distance / Cost)
   🟠 warning   = #f59e0b  (Warnings / Fuel)
   🔴 critical  = #ef4444  (Critical / Maintenance overdue)
   ⚫ offline   = #6b7280  (No data / None on duty)
   🟣 maintenance = #a855f7
──────────────────────────────────────────────────────────── */
const STATUS_TOKEN = {
  healthy:     '#22c55e',
  info:        '#3b82f6',
  warning:     '#f59e0b',
  critical:    '#ef4444',
  maintenance: '#a855f7',
  offline:     '#6b7280',
};

function KPICard({ icon: Icon, title, value, context, status, statusText }) {
  const accent = STATUS_TOKEN[status] ?? STATUS_TOKEN.info;
  const iconBg = `${accent}1a`; // 10% opacity background

  return (
    <Card className="kpi-card">
      <div className="kpi-card-top">
        <div className="kpi-card-icon" style={{ color: accent, backgroundColor: iconBg }}>
          <Icon size={18} strokeWidth={2} />
        </div>
        <span className="kpi-card-title text-caption">{title}</span>
      </div>

      <div className="kpi-card-value text-kpi-value">{value}</div>

      <div className="kpi-card-bottom">
        <span className="text-caption">{context}</span>
        <span className="kpi-card-status text-caption" style={{ color: accent }}>
          · {statusText}
        </span>
      </div>
    </Card>
  );
}

export default KPICard;
