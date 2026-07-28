import { BarChart3 } from 'lucide-react';
import PagePlaceholder from '../components/shared/PagePlaceholder';

export function AnalyticsPage() {
  return (
    <PagePlaceholder
      icon={<BarChart3 size={32} strokeWidth={1.5} />}
      title="Analytics & Reports"
      description="Fleet performance analytics, custom reports, trend analysis, and data export capabilities."
    />
  );
}
