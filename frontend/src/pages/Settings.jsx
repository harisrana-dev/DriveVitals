import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Settings as SettingsIcon,
  User,
  Shield,
  Activity,
  BarChart3,
  FlaskConical,
  Save,
  Check,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { settingsApi } from '../api/settingsApi';
import { Skeleton } from '../components/ui/Skeleton';

const TABS = [
  { key: 'account', label: 'Account', icon: User },
  { key: 'security', label: 'Security', icon: Shield },
  { key: 'system', label: 'System', icon: Activity },
  { key: 'analytics', label: 'Analytics', icon: BarChart3 },
  { key: 'digital-twin', label: 'Digital Twin', icon: FlaskConical },
];

// ────────────────────────────────────────────────────────────
// Tab: Account
// ────────────────────────────────────────────────────────────

function AccountTab({ account }) {
  if (!account) return <Skeleton style={{ height: 200, borderRadius: 12 }} />;

  const initials = (account.full_name || '')
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16,
        padding: 20, borderRadius: 12,
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border-light)',
      }}>
        <div style={{
          width: 56, height: 56, borderRadius: 12,
          background: 'var(--color-accent-light)',
          color: 'var(--color-accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 700, fontSize: 20, flexShrink: 0,
        }}>
          {initials}
        </div>
        <div>
          <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--color-text-primary)' }}>
            {account.full_name}
          </div>
          <div style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>
            {account.email}
          </div>
        </div>
      </div>

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12,
      }}>
        {[
          { label: 'Role', value: account.role?.charAt(0).toUpperCase() + account.role?.slice(1) },
          { label: 'User ID', value: account.user_id?.slice(0, 8) + '…' },
          { label: 'Status', value: 'Active' },
        ].map((item) => (
          <div key={item.label} style={{
            padding: 16, borderRadius: 10,
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border-light)',
          }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
              {item.label}
            </div>
            <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--color-text-primary)' }}>
              {item.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// Tab: Security
// ────────────────────────────────────────────────────────────

function SecurityTab() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{
        padding: 20, borderRadius: 12,
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border-light)',
      }}>
        <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--color-text-primary)', marginBottom: 8 }}>
          Session
        </div>
        <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
          You are currently authenticated with an active session.
          Session tokens are opaque, revocable, and expire automatically.
        </div>
      </div>
      <div style={{
        padding: 20, borderRadius: 12,
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border-light)',
      }}>
        <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--color-text-primary)', marginBottom: 8 }}>
          Password Management
        </div>
        <div style={{ fontSize: 13, color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
          Password change and reset functionality will be available in a future milestone.
        </div>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// Tab: System
// ────────────────────────────────────────────────────────────

function SystemTab({ system }) {
  if (!system) return <Skeleton style={{ height: 200, borderRadius: 12 }} />;

  const items = [
    { label: 'Application', value: system.app_name },
    { label: 'Version', value: system.version },
    { label: 'API Version', value: system.api_version },
    { label: 'Uptime', value: `${system.uptime_seconds}s` },
    { label: 'Database', value: system.database_status },
    { label: 'Runtime', value: system.runtime_status },
  ];

  return (
    <div style={{
      display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12,
    }}>
      {items.map((item) => (
        <div key={item.label} style={{
          padding: 16, borderRadius: 10,
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border-light)',
        }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
            {item.label}
          </div>
          <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--color-text-primary)' }}>
            {item.value}
          </div>
        </div>
      ))}
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// Tab: Analytics (editable)
// ────────────────────────────────────────────────────────────

function NumberInput({ label, value, onChange, min, max, step }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-text-muted)' }}>{label}</span>
      <input
        type="number"
        value={value ?? ''}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        min={min}
        max={max}
        step={step}
        style={{
          padding: '6px 10px', borderRadius: 6,
          border: '1px solid var(--color-border)',
          background: 'var(--color-bg)',
          color: 'var(--color-text-primary)',
          fontSize: 13, width: '100%',
        }}
      />
    </label>
  );
}

function SectionCard({ title, children }) {
  return (
    <div style={{
      padding: 16, borderRadius: 10,
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border-light)',
    }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 12 }}>
        {title}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10 }}>
        {children}
      </div>
    </div>
  );
}

function AnalyticsTab({ analytics, onSave, saving, saved, error }) {
  const [local, setLocal] = useState(() => analytics ? JSON.parse(JSON.stringify(analytics)) : null);
  const [dirty, setDirty] = useState(false);
  const [prevAnalytics, setPrevAnalytics] = useState(analytics);

  if (analytics !== prevAnalytics) {
    setPrevAnalytics(analytics);
    setLocal(analytics ? JSON.parse(JSON.stringify(analytics)) : null);
    setDirty(false);
  }

  const update = useCallback((section, key, value) => {
    setLocal((prev) => {
      const next = { ...prev };
      next[section] = { ...next[section], [key]: value };
      return next;
    });
    setDirty(true);
  }, []);

  const handleSave = useCallback(() => {
    if (local) onSave(local);
  }, [local, onSave]);

  if (!local) return <Skeleton style={{ height: 400, borderRadius: 12 }} />;

  const vh = local.vehicle_health || {};
  const ds = local.driver_statistics || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Vehicle Health */}
      <SectionCard title="Status Thresholds">
        <NumberInput label="Healthy Min" value={vh.status?.healthy_min}
          onChange={(v) => update('vehicle_health', 'status', { ...vh.status, healthy_min: v })}
          min={0} max={100} step={1} />
        <NumberInput label="Warning Min" value={vh.status?.warning_min}
          onChange={(v) => update('vehicle_health', 'status', { ...vh.status, warning_min: v })}
          min={0} max={100} step={1} />
        <NumberInput label="Window Size" value={vh.window_size}
          onChange={(v) => update('vehicle_health', 'window_size', v)}
          min={1} max={200} step={1} />
      </SectionCard>

      <SectionCard title="Engine Thresholds">
        <NumberInput label="Redline RPM" value={vh.engine?.redline_rpm}
          onChange={(v) => update('vehicle_health', 'engine', { ...vh.engine, redline_rpm: v })}
          min={1000} max={10000} step={100} />
        <NumberInput label="Sustained RPM" value={vh.engine?.sustained_rpm}
          onChange={(v) => update('vehicle_health', 'engine', { ...vh.engine, sustained_rpm: v })}
          min={1000} max={8000} step={100} />
        <NumberInput label="Overheat Temp °C" value={vh.engine?.overheat_temp_c}
          onChange={(v) => update('vehicle_health', 'engine', { ...vh.engine, overheat_temp_c: v })}
          min={60} max={150} step={1} />
      </SectionCard>

      <SectionCard title="Brake Thresholds">
        <NumberInput label="Harsh Pressure" value={vh.brake?.harsh_brake_pressure}
          onChange={(v) => update('vehicle_health', 'brake', { ...vh.brake, harsh_brake_pressure: v })}
          min={0} max={1} step={0.05} />
        <NumberInput label="Hard Pressure" value={vh.brake?.hard_brake_pressure}
          onChange={(v) => update('vehicle_health', 'brake', { ...vh.brake, hard_brake_pressure: v })}
          min={0} max={1} step={0.05} />
      </SectionCard>

      <SectionCard title="Driver Statistics — Safety">
        <NumberInput label="Weight: Hard Brake" value={ds.safety?.weight_hard_brake}
          onChange={(v) => update('driver_statistics', 'safety', { ...ds.safety, weight_hard_brake: v })}
          min={0} max={10} step={0.5} />
        <NumberInput label="Weight: Overspeed" value={ds.safety?.weight_overspeed}
          onChange={(v) => update('driver_statistics', 'safety', { ...ds.safety, weight_overspeed: v })}
          min={0} max={10} step={0.5} />
        <NumberInput label="Density Sensitivity" value={ds.safety?.density_sensitivity}
          onChange={(v) => update('driver_statistics', 'safety', { ...ds.safety, density_sensitivity: v })}
          min={0} max={2} step={0.05} />
      </SectionCard>

      <SectionCard title="Driver Statistics — Aggression">
        <NumberInput label="Max Density" value={ds.aggression?.max_density}
          onChange={(v) => update('driver_statistics', 'aggression', { ...ds.aggression, max_density: v })}
          min={0.1} max={10} step={0.1} />
      </SectionCard>

      <SectionCard title="Driver Statistics — Efficiency">
        <NumberInput label="Max Events / km" value={ds.efficiency?.max_events_per_km}
          onChange={(v) => update('driver_statistics', 'efficiency', { ...ds.efficiency, max_events_per_km: v })}
          min={0.1} max={10} step={0.1} />
      </SectionCard>

      {/* Status bar */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 16px', borderRadius: 10,
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border-light)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
          {dirty && <span style={{ color: 'var(--color-amber)' }}>Unsaved changes</span>}
          {saved && <span style={{ color: 'var(--color-green)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <Check size={14} /> Saved
          </span>}
          {error && <span style={{ color: 'var(--color-red)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <AlertCircle size={14} /> {error}
          </span>}
        </div>
        <button
          onClick={handleSave}
          disabled={saving || !dirty}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '8px 16px', borderRadius: 8,
            background: dirty ? 'var(--color-accent)' : 'var(--color-surface)',
            color: dirty ? '#fff' : 'var(--color-text-muted)',
            border: '1px solid var(--color-border)',
            fontSize: 13, fontWeight: 600, cursor: saving ? 'wait' : (dirty ? 'pointer' : 'default'),
            opacity: saving ? 0.7 : 1,
            transition: 'all 0.15s ease',
          }}
        >
          {saving ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Save size={14} />}
          {saving ? 'Saving…' : 'Save changes'}
        </button>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// Tab: Digital Twin (M4 placeholder)
// ────────────────────────────────────────────────────────────

function DigitalTwinTab() {
  return (
    <div style={{
      padding: 32, borderRadius: 12,
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border-light)',
      textAlign: 'center',
    }}>
      <FlaskConical size={32} style={{ color: 'var(--color-accent)', marginBottom: 12 }} />
      <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 8 }}>
        Digital Twin Lab
      </div>
      <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', maxWidth: 400, margin: '0 auto', lineHeight: 1.6 }}>
        Configure vehicles, drivers, routes, assignments, and simulation behavior
        from a dedicated Digital Twin workspace.
      </div>
      <Link
        to="/digital-twin-lab"
        style={{
          marginTop: 20, display: 'inline-block',
          padding: '8px 18px', borderRadius: 8,
          background: 'var(--color-accent)', color: '#fff',
          textDecoration: 'none', fontSize: 13, fontWeight: 600,
        }}
      >
        Open Digital Twin Lab
      </Link>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// Main Settings Page
// ────────────────────────────────────────────────────────────

export function SettingsPage() {
  useAuth(); // ensure auth context is available
  const [activeTab, setActiveTab] = useState('account');
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const result = await settingsApi.getSettings();
        if (!cancelled) setSettings(result?.data ?? null);
      } catch (err) {
        if (!cancelled) setError(err?.message || 'Failed to load settings');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const handleSaveAnalytics = useCallback(async (data) => {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const result = await settingsApi.updateCategory('analytics', data);
      setSettings((prev) => ({
        ...prev,
        analytics: result?.data?.data ?? data,
      }));
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err?.detail || err?.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  }, []);

  return (
    <div style={{ padding: '0 28px 40px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 8 }}>
        <div style={{
          width: 40, height: 40, borderRadius: 10,
          background: 'var(--color-accent-subtle)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--color-accent)', flexShrink: 0,
        }}>
          <SettingsIcon size={20} strokeWidth={1.7} />
        </div>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 600, color: 'var(--color-text-primary)', margin: 0 }}>
            Settings
          </h2>
          <p style={{ fontSize: 12.5, color: 'var(--color-text-muted)', margin: '2px 0 0' }}>
            Fleet administration and system configuration
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex', gap: 4, marginTop: 20, marginBottom: 20,
        borderBottom: '1px solid var(--color-border-light)',
        paddingBottom: 0, overflowX: 'auto',
      }}>
        {TABS.map(({ key, label, icon: Icon }) => {
          const isActive = activeTab === key;
          return (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '8px 14px', borderRadius: '8px 8px 0 0',
                border: '1px solid transparent',
                borderBottom: isActive ? '2px solid var(--color-accent)' : '2px solid transparent',
                background: 'transparent',
                color: isActive ? 'var(--color-accent)' : 'var(--color-text-muted)',
                fontSize: 13, fontWeight: isActive ? 600 : 400,
                cursor: 'pointer', whiteSpace: 'nowrap',
                marginBottom: -1, transition: 'all 0.15s ease',
              }}
            >
              <Icon size={15} />
              {label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Skeleton style={{ height: 120, borderRadius: 12 }} />
          <Skeleton style={{ height: 80, borderRadius: 12 }} />
          <Skeleton style={{ height: 80, borderRadius: 12 }} />
        </div>
      ) : (
        <>
          {activeTab === 'account' && <AccountTab account={settings?.account} />}
          {activeTab === 'security' && <SecurityTab />}
          {activeTab === 'system' && <SystemTab system={settings?.system} />}
          {activeTab === 'analytics' && (
            <AnalyticsTab
              analytics={settings?.analytics}
              onSave={handleSaveAnalytics}
              saving={saving}
              saved={saved}
              error={error}
            />
          )}
          {activeTab === 'digital-twin' && <DigitalTwinTab />}
        </>
      )}
    </div>
  );
}

export default SettingsPage;
