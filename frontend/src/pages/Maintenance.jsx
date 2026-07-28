import { Wrench } from 'lucide-react';
import PagePlaceholder from '../components/shared/PagePlaceholder';

export function MaintenancePage() {
  return (
    <PagePlaceholder
      icon={<Wrench size={32} strokeWidth={1.5} />}
      title="Maintenance"
      description="Schedule and track vehicle maintenance, service history, parts inventory, and vendor management."
    />
  );
}
