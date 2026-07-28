import { Users } from 'lucide-react';
import PagePlaceholder from '../components/shared/PagePlaceholder';

export function DriversPage() {
  return (
    <PagePlaceholder
      icon={<Users size={32} strokeWidth={1.5} />}
      title="Driver Management"
      description="View driver profiles, safety scores, driving behavior analytics, and driver-specific reports."
    />
  );
}
