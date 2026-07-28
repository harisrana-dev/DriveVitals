import { Settings as SettingsIcon } from 'lucide-react';
import PagePlaceholder from '../components/shared/PagePlaceholder';

export function SettingsPage() {
  return (
    <PagePlaceholder
      icon={<SettingsIcon size={32} strokeWidth={1.5} />}
      title="Settings"
      description="Configure your account, notification preferences, fleet settings, integrations, and access controls."
    />
  );
}
