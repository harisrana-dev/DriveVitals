import { Radio } from 'lucide-react';
import PagePlaceholder from '../components/shared/PagePlaceholder';

export function LiveTelemetryPage() {
  return (
    <PagePlaceholder
      icon={<Radio size={32} strokeWidth={1.5} />}
      title="Live Telemetry"
      description="Real-time vehicle telemetry streaming with detailed sensor data, engine diagnostics, and CAN bus information."
    />
  );
}
