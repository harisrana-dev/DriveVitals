import { MapPin } from 'lucide-react';
import PagePlaceholder from '../components/shared/PagePlaceholder';

export function TripsPage() {
  return (
    <PagePlaceholder
      icon={<MapPin size={32} strokeWidth={1.5} />}
      title="Trip History"
      description="Review completed and ongoing trips, route details, distance traveled, and trip-specific analytics."
    />
  );
}
