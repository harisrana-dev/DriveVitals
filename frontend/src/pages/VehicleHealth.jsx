import { HeartPulse } from 'lucide-react';
import PagePlaceholder from '../components/shared/PagePlaceholder';

export function VehicleHealthPage() {
  return (
    <PagePlaceholder
      icon={<HeartPulse size={32} strokeWidth={1.5} />}
      title="Vehicle Health"
      description="Detailed vehicle health diagnostics, DTC codes, component monitoring, and predictive maintenance alerts."
    />
  );
}
