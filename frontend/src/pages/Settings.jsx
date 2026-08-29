import { Settings as SettingsIcon } from 'lucide-react';

const SETTINGS_SECTIONS = [
  { key: 'identity', label: 'Access & Identity' },
  { key: 'simulation', label: 'Simulation / Digital Twin' },
  { key: 'fleet', label: 'Fleet Configuration' },
  { key: 'drivers', label: 'Driver Configuration' },
  { key: 'routes', label: 'Route Configuration' },
  { key: 'runtime', label: 'Runtime Controls' },
  { key: 'system', label: 'System Information' },
];

export function SettingsPage() {
  return (
    <div style={{ padding: '0 28px 40px' }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        marginBottom: 8,
      }}>
        <div style={{
          width: 40,
          height: 40,
          borderRadius: 10,
          background: 'var(--color-accent-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-accent)',
          flexShrink: 0,
        }}>
          <SettingsIcon size={20} strokeWidth={1.7} />
        </div>
        <div>
          <h2 style={{
            fontSize: 20,
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            margin: 0,
          }}>
            Settings
          </h2>
          <p style={{
            fontSize: 12.5,
            color: 'var(--color-text-muted)',
            margin: '2px 0 0',
          }}>
            Fleet administration and system configuration
          </p>
        </div>
      </div>

      <p style={{
        fontSize: 13.5,
        color: 'var(--color-text-secondary)',
        maxWidth: 640,
        lineHeight: 1.6,
        margin: '0 0 28px',
      }}>
        Settings is restricted to fleet administrators. Configuration
        sections arrive in later milestones — they are listed as placeholders
        until the Digital Twin Lab is built on top of the M2 security boundary.
      </p>

      {SETTINGS_SECTIONS.map((section) => (
        <div key={section.key} style={{
          border: '1px solid var(--color-border-light)',
          borderRadius: 12,
          padding: '16px 20px',
          marginBottom: 12,
          background: 'var(--color-surface)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 16,
        }}>
          <div>
            <div style={{
              fontSize: 14,
              fontWeight: 500,
              color: 'var(--color-text-primary)',
              marginBottom: 2,
            }}>
              {section.label}
            </div>
            <div style={{
              fontSize: 12,
              color: 'var(--color-text-muted)',
            }}>
              Coming in a later milestone
            </div>
          </div>
          <div style={{
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: '0.06em',
            color: 'var(--color-text-muted)',
            textTransform: 'uppercase',
            padding: '4px 10px',
            borderRadius: 6,
            border: '1px solid var(--color-border-light)',
            flexShrink: 0,
          }}>
            Placeholder
          </div>
        </div>
      ))}
    </div>
  );
}

export default SettingsPage;