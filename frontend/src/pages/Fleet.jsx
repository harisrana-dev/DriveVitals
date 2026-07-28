import { Truck } from 'lucide-react';
import PagePlaceholder from '../components/shared/PagePlaceholder';

export function FleetPage() {
  return (
    <PagePlaceholder
      icon={<Truck size={32} strokeWidth={1.5} />}
      title="Fleet Management"
      description="View and manage your entire vehicle fleet, assign vehicles to drivers, and monitor vehicle details."
    />
  );
}
