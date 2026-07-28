import { AlertTriangle } from 'lucide-react';
import PagePlaceholder from '../components/shared/PagePlaceholder';

export function AlertsPage() {
  return (
    <PagePlaceholder
      icon={<AlertTriangle size={32} strokeWidth={1.5} />}
      title="Alerts & Notifications"
      description="Monitor fleet alerts, configure notification rules, and review alert history across your fleet."
    />
  );
}
