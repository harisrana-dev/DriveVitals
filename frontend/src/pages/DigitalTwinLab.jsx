import { useState, useEffect, useCallback } from 'react';
import {
  FlaskConical,
  Activity,
  Play,
  Square,
  RotateCcw,
  Truck,
  Link2,
  ListTree,
  Plus,
  Trash2,
  Save,
  AlertCircle,
  Loader2,
  Zap,
  Info,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { digitalTwinApi } from '../api/digitalTwinApi';
import { Skeleton } from '../components/ui/Skeleton';

const TABS = [
  { key: 'overview', label: 'Overview', icon: Activity },
  { key: 'fleet', label: 'Fleet', icon: Truck },
  { key: 'assignments', label: 'Assignments', icon: Link2 },
  { key: 'scenarios', label: 'Scenarios', icon: ListTree },
];

// ────────────────────────────────────────────────────────────
// Shared bits
// ────────────────────────────────────────────────────────────

function Card({ title, children, style, action }) {
  return (
    <div style={{
      padding: 16, borderRadius: 12,
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border-light)',
      ...style,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>{title}</div>
        {action}
      </div>
      {children}
    </div>
  );
}

function Badge({ children, tone = 'neutral' }) {
  const colors = {
    neutral: { background: 'var(--color-surface)', color: 'var(--color-text-muted)', border: '1px solid var(--color-border)' },
    green: { background: 'rgba(34,197,94,0.12)', color: 'var(--color-green)', border: '1px solid rgba(34,197,94,0.3)' },
    amber: { background: 'rgba(245,158,11,0.12)', color: 'var(--color-amber)', border: '1px solid rgba(245,158,11,0.3)' },
    red: { background: 'rgba(239,68,68,0.12)', color: 'var(--color-red)', border: '1px solid rgba(239,68,68,0.3)' },
    accent: { background: 'var(--color-accent-subtle)', color: 'var(--color-accent)', border: '1px solid var(--color-accent)' },
  };
  const c = colors[tone] || colors.neutral;
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 999,
      fontSize: 10.5, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em',
      ...c,
    }}>
      {children}
    </span>
  );
}

function EmptyRow({ text }) {
  return (
    <div style={{ padding: '20px 8px', textAlign: 'center', fontSize: 13, color: 'var(--color-text-muted)' }}>
      {text}
    </div>
  );
}

function StatusPill({ running }) {
  return running
    ? <Badge tone="green"><span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}><span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-green)', display: 'inline-block' }} />Running</span></Badge>
    : <Badge tone="neutral">Idle</Badge>;
}

// ────────────────────────────────────────────────────────────
// Overview tab
// ────────────────────────────────────────────────────────────

function OverviewTab({ status, onLaunch, onStop, onReset, busy }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Card title="Simulation status">
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12,
        }}>
          {[
            { label: 'Status', value: status?.running ? 'Running' : 'Idle' },
            { label: 'Vehicles', value: status?.vehicles ?? '0' },
            { label: 'Scenario', value: status?.scenario_name || status?.scenario_id || '—' },
            { label: 'Run', value: status?.run_id ? status.run_id.slice(0, 8) : '—' },
          ].map((item) => (
            <div key={item.label} style={{
              padding: 14, borderRadius: 10,
              background: 'var(--color-bg)',
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

        <div style={{ display: 'flex', gap: 10, marginTop: 16, flexWrap: 'wrap' }}>
          <button
            onClick={onLaunch}
            disabled={busy}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '8px 16px', borderRadius: 8,
              background: 'var(--color-accent)', color: '#fff',
              border: '1px solid var(--color-accent)',
              fontSize: 13, fontWeight: 600, cursor: busy ? 'wait' : 'pointer',
            }}
          >
            {busy ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={14} />}
            Launch scenario
          </button>
          <button
            onClick={onStop}
            disabled={busy || !status?.running}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '8px 16px', borderRadius: 8,
              background: 'var(--color-surface)', color: 'var(--color-text-primary)',
              border: '1px solid var(--color-border)',
              fontSize: 13, fontWeight: 600,
              cursor: busy || !status?.running ? 'not-allowed' : 'pointer',
              opacity: status?.running ? 1 : 0.5,
            }}
          >
            <Square size={14} />
            Stop
          </button>
          <button
            onClick={onReset}
            disabled={busy}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '8px 16px', borderRadius: 8,
              background: 'var(--color-surface)', color: 'var(--color-text-primary)',
              border: '1px solid var(--color-border)',
              fontSize: 13, fontWeight: 600, cursor: busy ? 'wait' : 'pointer',
            }}
          >
            <RotateCcw size={14} />
            Reset
          </button>
        </div>
      </Card>

      <Card title="Launching a scenario">
        <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
          Select a scenario on the <strong>Scenarios</strong> tab and activate it (its status
          becomes <em>Ready</em>), then return here and choose <strong>Launch scenario</strong>.
          The scenario's fleet assignment is applied live to the simulation runtime and telemetry
          is regenerated with the configured vehicle characteristics.
        </div>
      </Card>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// Generic management list + create form
// ────────────────────────────────────────────────────────────

function ManagementList({ items, columns, renderActions }) {
  if (!items.length) return <EmptyRow text="No records yet. Create one below." />;
  return (
    <div style={{
      border: '1px solid var(--color-border-light)', borderRadius: 10, overflow: 'hidden',
    }}>
      {items.map((item, idx) => (
        <div key={item.id} style={{
          display: 'grid', gridTemplateColumns: `1fr auto`, gap: 12, alignItems: 'center',
          padding: '10px 12px',
          borderTop: idx === 0 ? 'none' : '1px solid var(--color-border-light)',
        }}>
          <div style={{
            display: 'grid', gridTemplateColumns: columns, gap: 12, alignItems: 'center', minWidth: 0,
          }}>
            {item.cells.map((cell, ci) => (
              <div key={ci} style={{ fontSize: 13, color: 'var(--color-text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {cell}
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            {renderActions && renderActions(item)}
          </div>
        </div>
      ))}
    </div>
  );
}

function driverDisplayName(d) {
  const full = [d.first_name, d.last_name].filter(Boolean).join(' ').trim();
  return full || '—';
}

// ────────────────────────────────────────────────────────────
// Fleet tab
// ────────────────────────────────────────────────────────────

function FleetTab({ drivers, vehicles, routes, onRefresh, notice, onNotice }) {
  const [driverForm, setDriverForm] = useState({ driver_id: '', first_name: '', last_name: '', behavior_profile: 'eco' });
  const [vehicleForm, setVehicleForm] = useState({ vehicle_id: '', manufacturer: '', model: '' });
  const [routeForm, setRouteForm] = useState({ route_id: '', origin: '', destination: '', estimated_distance_km: 10 });
  const [saving, setSaving] = useState(false);

  const submitDriver = useCallback(async () => {
    if (!driverForm.driver_id || !driverForm.first_name) return;
    setSaving(true);
    try {
      await digitalTwinApi.createDriver({ ...driverForm, behavior_profile: driverForm.behavior_profile });
      onNotice('Driver created');
      setDriverForm({ driver_id: '', first_name: '', last_name: '', behavior_profile: 'eco' });
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Failed to create driver');
    } finally {
      setSaving(false);
    }
  }, [driverForm, onRefresh, onNotice]);

  const submitVehicle = useCallback(async () => {
    if (!vehicleForm.vehicle_id || !vehicleForm.manufacturer || !vehicleForm.model) return;
    setSaving(true);
    try {
      await digitalTwinApi.createVehicle(vehicleForm);
      onNotice('Vehicle created');
      setVehicleForm({ vehicle_id: '', manufacturer: '', model: '' });
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Failed to create vehicle');
    } finally {
      setSaving(false);
    }
  }, [vehicleForm, onRefresh, onNotice]);

  const submitRoute = useCallback(async () => {
    if (!routeForm.route_id || !routeForm.origin || !routeForm.destination) return;
    setSaving(true);
    try {
      await digitalTwinApi.createRoute({ ...routeForm, estimated_distance_km: parseFloat(routeForm.estimated_distance_km) || 0 });
      onNotice('Route created');
      setRouteForm({ route_id: '', origin: '', destination: '', estimated_distance_km: 10 });
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Failed to create route');
    } finally {
      setSaving(false);
    }
  }, [routeForm, onRefresh, onNotice]);

  const removeDriver = useCallback(async (id) => {
    setSaving(true);
    try {
      await digitalTwinApi.deleteDriver(id);
      onNotice('Driver deleted');
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Delete failed');
    } finally {
      setSaving(false);
    }
  }, [onRefresh, onNotice]);

  const removeVehicle = useCallback(async (id) => {
    setSaving(true);
    try {
      await digitalTwinApi.deleteVehicle(id);
      onNotice('Vehicle deleted');
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Delete failed');
    } finally {
      setSaving(false);
    }
  }, [onRefresh, onNotice]);

  const removeRoute = useCallback(async (id) => {
    setSaving(true);
    try {
      await digitalTwinApi.deleteRoute(id);
      onNotice('Route deleted');
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Delete failed');
    } finally {
      setSaving(false);
    }
  }, [onRefresh, onNotice]);

  const inputStyle = {
    padding: '6px 10px', borderRadius: 6,
    border: '1px solid var(--color-border)',
    background: 'var(--color-bg)',
    color: 'var(--color-text-primary)',
    fontSize: 12.5, width: '100%',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {notice && (
        <div style={{
          padding: '8px 12px', borderRadius: 8, fontSize: 12.5,
          background: 'var(--color-accent-subtle)', color: 'var(--color-accent)',
          border: '1px solid var(--color-accent)',
        }}>
          {notice}
        </div>
      )}

      <Card title="Vehicles">
        <ManagementList
          items={vehicles.map((v) => ({
            id: v.vehicle_id,
            cells: [v.vehicle_id, `${v.manufacturer} ${v.model}`, v.year || '—'],
          }))}
          columns="0.8fr 1.2fr 0.6fr"
          renderActions={({ id }) => (
            <button onClick={() => removeVehicle(id)} title="Delete" style={iconBtn}>
              <Trash2 size={14} />
            </button>
          )}
        />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 8, marginTop: 12, alignItems: 'end' }}>
          <input placeholder="ID" value={vehicleForm.vehicle_id} onChange={(e) => setVehicleForm({ ...vehicleForm, vehicle_id: e.target.value })} style={inputStyle} />
          <input placeholder="Manufacturer" value={vehicleForm.manufacturer} onChange={(e) => setVehicleForm({ ...vehicleForm, manufacturer: e.target.value })} style={inputStyle} />
          <input placeholder="Model" value={vehicleForm.model} onChange={(e) => setVehicleForm({ ...vehicleForm, model: e.target.value })} style={inputStyle} />
          <button onClick={submitVehicle} disabled={saving} style={addBtn}>
            {saving ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Plus size={14} />}
          </button>
        </div>
      </Card>

      <Card title="Drivers">
        <ManagementList
          items={drivers.map((d) => ({
            id: d.driver_id,
            cells: [d.driver_id, driverDisplayName(d), d.behavior_profile || '—'],
          }))}
          columns="0.8fr 1.2fr 0.8fr"
          renderActions={({ id }) => (
            <button onClick={() => removeDriver(id)} title="Delete" style={iconBtn}>
              <Trash2 size={14} />
            </button>
          )}
        />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr auto', gap: 8, marginTop: 12, alignItems: 'end' }}>
          <input placeholder="ID" value={driverForm.driver_id} onChange={(e) => setDriverForm({ ...driverForm, driver_id: e.target.value })} style={inputStyle} />
          <input placeholder="First name" value={driverForm.first_name} onChange={(e) => setDriverForm({ ...driverForm, first_name: e.target.value })} style={inputStyle} />
          <input placeholder="Last name" value={driverForm.last_name} onChange={(e) => setDriverForm({ ...driverForm, last_name: e.target.value })} style={inputStyle} />
          <select value={driverForm.behavior_profile} onChange={(e) => setDriverForm({ ...driverForm, behavior_profile: e.target.value })} style={inputStyle}>
            <option value="eco">Eco</option>
            <option value="balanced">Balanced</option>
            <option value="aggressive">Aggressive</option>
            <option value="cautious">Cautious</option>
          </select>
          <button onClick={submitDriver} disabled={saving} style={addBtn}>
            {saving ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Plus size={14} />}
          </button>
        </div>
      </Card>

      <Card title="Routes">
        <ManagementList
          items={routes.map((r) => ({
            id: r.route_id,
            cells: [r.route_id, `${r.origin} → ${r.destination}`, `${r.estimated_distance_km} km`],
          }))}
          columns="0.8fr 1.4fr 0.6fr"
          renderActions={({ id }) => (
            <button onClick={() => removeRoute(id)} title="Delete" style={iconBtn}>
              <Trash2 size={14} />
            </button>
          )}
        />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 0.8fr auto', gap: 8, marginTop: 12, alignItems: 'end' }}>
          <input placeholder="ID" value={routeForm.route_id} onChange={(e) => setRouteForm({ ...routeForm, route_id: e.target.value })} style={inputStyle} />
          <input placeholder="Origin" value={routeForm.origin} onChange={(e) => setRouteForm({ ...routeForm, origin: e.target.value })} style={inputStyle} />
          <input placeholder="Destination" value={routeForm.destination} onChange={(e) => setRouteForm({ ...routeForm, destination: e.target.value })} style={inputStyle} />
          <input type="number" placeholder="Distance km" value={routeForm.estimated_distance_km} onChange={(e) => setRouteForm({ ...routeForm, estimated_distance_km: e.target.value })} style={inputStyle} />
          <button onClick={submitRoute} disabled={saving} style={addBtn}>
            {saving ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Plus size={14} />}
          </button>
        </div>
      </Card>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// Assignments tab
// ────────────────────────────────────────────────────────────

function AssignmentsTab({ assignments, drivers, vehicles, routes, onRefresh, onNotice }) {
  const [form, setForm] = useState({ assignment_id: '', driver_id: '', vehicle_id: '', route_id: '', is_active: true });
  const [saving, setSaving] = useState(false);

  const selectStyle = {
    padding: '6px 10px', borderRadius: 6,
    border: '1px solid var(--color-border)',
    background: 'var(--color-bg)',
    color: 'var(--color-text-primary)',
    fontSize: 12.5, width: '100%',
  };

  const submit = useCallback(async () => {
    if (!form.assignment_id || !form.driver_id || !form.vehicle_id || !form.route_id) {
      onNotice('All fields are required');
      return;
    }
    setSaving(true);
    try {
      await digitalTwinApi.createAssignment({
        assignment_id: form.assignment_id,
        driver_id: form.driver_id,
        vehicle_id: form.vehicle_id,
        route_id: form.route_id,
        is_active: Boolean(form.is_active),
      });
      onNotice('Assignment created');
      setForm({ assignment_id: '', driver_id: '', vehicle_id: '', route_id: '', is_active: true });
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Failed to create assignment');
    } finally {
      setSaving(false);
    }
  }, [form, onRefresh, onNotice]);

  const remove = useCallback(async (id) => {
    setSaving(true);
    try {
      await digitalTwinApi.deleteAssignment(id);
      onNotice('Assignment deleted');
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Delete failed');
    } finally {
      setSaving(false);
    }
  }, [onRefresh, onNotice]);

  const driverLabel = (id) => {
    const d = drivers.find((x) => x.driver_id === id);
    return d ? driverDisplayName(d) : id;
  };
  const vehicleLabel = (id) => {
    const v = vehicles.find((x) => x.vehicle_id === id);
    return v ? `${v.manufacturer} ${v.model}` : id;
  };
  const routeLabel = (id) => {
    const r = routes.find((x) => x.route_id === id);
    return r ? `${r.origin} → ${r.destination}` : id;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Card title="Assignments">
        <ManagementList
          items={assignments.map((a) => ({
            id: a.assignment_id,
            cells: [a.assignment_id, driverLabel(a.driver_id), vehicleLabel(a.vehicle_id), routeLabel(a.route_id), a.is_active ? <Badge tone="green">Active</Badge> : <Badge>Inactive</Badge>],
          }))}
          columns="0.9fr 1fr 1fr 1fr 0.6fr"
          renderActions={({ id }) => (
            <button onClick={() => remove(id)} title="Delete" style={iconBtn}>
              <Trash2 size={14} />
            </button>
          )}
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr auto', gap: 8, marginTop: 12, alignItems: 'end' }}>
          <input placeholder="Assignment ID" value={form.assignment_id} onChange={(e) => setForm({ ...form, assignment_id: e.target.value })}
            style={{ ...selectStyle, border: '1px solid var(--color-border)' }} />
          <select value={form.driver_id} onChange={(e) => setForm({ ...form, driver_id: e.target.value })} style={selectStyle}>
            <option value="">Driver…</option>
            {drivers.map((d) => <option key={d.driver_id} value={d.driver_id}>{d.driver_id} · {driverDisplayName(d)}</option>)}
          </select>
          <select value={form.vehicle_id} onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })} style={selectStyle}>
            <option value="">Vehicle…</option>
            {vehicles.map((v) => <option key={v.vehicle_id} value={v.vehicle_id}>{v.vehicle_id} · {v.manufacturer} {v.model}</option>)}
          </select>
          <select value={form.route_id} onChange={(e) => setForm({ ...form, route_id: e.target.value })} style={selectStyle}>
            <option value="">Route…</option>
            {routes.map((r) => <option key={r.route_id} value={r.route_id}>{r.route_id} · {r.origin}→{r.destination}</option>)}
          </select>
          <button onClick={submit} disabled={saving} style={addBtn}>
            {saving ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Plus size={14} />}
          </button>
        </div>
      </Card>
    </div>
  );
}

// ────────────────────────────────────────────────────────────
// Scenarios tab
// ────────────────────────────────────────────────────────────

const STATUS_TONES = {
  draft: 'neutral',
  ready: 'accent',
  running: 'green',
  completed: 'neutral',
  stopped: 'amber',
};

const BEHAVIOR_DESCRIPTIONS = {
  standard: 'Baseline simulated driving behavior.',
  eco: 'Smoother driving behavior intended to reduce fuel consumption.',
  aggressive: 'More aggressive acceleration and driving variation.',
  cautious: 'More conservative driving behavior with gentler dynamics.',
};

function resolveAssignment(a, drivers, vehicles, routes) {
  const driver = drivers.find((d) => d.driver_id === a.driver_id) || null;
  const vehicle = vehicles.find((v) => v.vehicle_id === a.vehicle_id) || null;
  const route = routes.find((r) => r.route_id === a.route_id) || null;
  return { driver, vehicle, route };
}

function BehaviorBadge({ profile }) {
  const tone = profile === 'aggressive' ? 'red'
    : profile === 'eco' ? 'green'
    : profile === 'cautious' ? 'amber'
    : 'neutral';
  return <Badge tone={tone}>{profile || 'standard'}</Badge>;
}

function AssignmentCard({ assignment, drivers, vehicles, routes, onRemove }) {
  const { driver, vehicle, route } = resolveAssignment(assignment, drivers, vehicles, routes);

  return (
    <div style={{
      padding: 14, borderRadius: 10,
      border: '1px solid var(--color-border-light)',
      background: 'var(--color-bg)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Driver */}
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
              Driver
            </div>
            {driver ? (
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  {driverDisplayName(driver)}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 3 }}>
                  <span style={{ fontSize: 11.5, color: 'var(--color-text-muted)' }}>Behavior:</span>
                  <BehaviorBadge profile={driver.behavior_profile} />
                </div>
                {BEHAVIOR_DESCRIPTIONS[driver.behavior_profile] && (
                  <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', marginTop: 3, fontStyle: 'italic' }}>
                    {BEHAVIOR_DESCRIPTIONS[driver.behavior_profile]}
                  </div>
                )}
              </div>
            ) : (
              <span style={{ fontSize: 12.5, color: 'var(--color-text-muted)' }}>{assignment.driver_id}</span>
            )}
          </div>

          {/* Vehicle */}
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
              Vehicle
            </div>
            {vehicle ? (
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  {vehicle.manufacturer} {vehicle.model}
                  {vehicle.year ? <span style={{ fontWeight: 400, color: 'var(--color-text-muted)', marginLeft: 4 }}>{vehicle.year}</span> : null}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 14px', marginTop: 4, fontSize: 11.5, color: 'var(--color-text-muted)' }}>
                  <span>Fuel efficiency: <strong style={{ color: 'var(--color-text-primary)' }}>{vehicle.fuel_efficiency_factor}x</strong> baseline</span>
                  <span>Acceleration: <strong style={{ color: 'var(--color-text-primary)' }}>{vehicle.acceleration_response}x</strong> baseline</span>
                  <span>Tank: <strong style={{ color: 'var(--color-text-primary)' }}>{vehicle.tank_capacity_liters} L</strong></span>
                </div>
              </div>
            ) : (
              <span style={{ fontSize: 12.5, color: 'var(--color-text-muted)' }}>{assignment.vehicle_id}</span>
            )}
          </div>

          {/* Route */}
          <div>
            <div style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
              Route
            </div>
            {route ? (
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  {route.origin} → {route.destination}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 14px', marginTop: 4, fontSize: 11.5, color: 'var(--color-text-muted)' }}>
                  <span>Distance: <strong style={{ color: 'var(--color-text-primary)' }}>{route.estimated_distance_km} km</strong></span>
                  <span>Speed limit: <strong style={{ color: 'var(--color-text-primary)' }}>{route.speed_limit_kmh} km/h</strong></span>
                  <span>Status: {route.is_active ? <Badge tone="green">Active</Badge> : <Badge>Inactive</Badge>}</span>
                </div>
              </div>
            ) : (
              <span style={{ fontSize: 12.5, color: 'var(--color-text-muted)' }}>{assignment.route_id}</span>
            )}
          </div>
        </div>

        <button onClick={() => onRemove(assignment.assignment_id)} title="Remove assignment" style={iconBtn}>
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  );
}

function ScenarioPreview({ scenarioAssignments, drivers, vehicles, routes }) {
  const resolved = scenarioAssignments.map((a) => resolveAssignment(a, drivers, vehicles, routes));
  const uniqueDrivers = [...new Set(resolved.filter((r) => r.driver).map((r) => r.driver))];
  const uniqueVehicles = [...new Set(resolved.filter((r) => r.vehicle).map((r) => r.vehicle))];
  const uniqueRoutes = [...new Set(resolved.filter((r) => r.route).map((r) => r.route))];

  const dominantBehavior = uniqueDrivers.length === 1
    ? uniqueDrivers[0].behavior_profile
    : uniqueDrivers.length > 1
      ? [...new Set(uniqueDrivers.map((d) => d.behavior_profile))]
      : [];

  return (
    <div style={{
      padding: 14, borderRadius: 10,
      background: 'var(--color-accent-subtle)',
      border: '1px solid var(--color-accent)',
    }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-accent)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Simulation preview
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 10, marginBottom: 10 }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>Fleet</div>
          <div style={{ fontSize: 13, color: 'var(--color-text-primary)' }}>
            {uniqueDrivers.length} driver{uniqueDrivers.length !== 1 ? 's' : ''} · {uniqueVehicles.length} vehicle{uniqueVehicles.length !== 1 ? 's' : ''} · {uniqueRoutes.length} route{uniqueRoutes.length !== 1 ? 's' : ''}
          </div>
        </div>
        {dominantBehavior.length > 0 && (
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>Driving behavior</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {(Array.isArray(dominantBehavior) ? dominantBehavior : [dominantBehavior]).map((b) => (
                <BehaviorBadge key={b} profile={b} />
              ))}
            </div>
          </div>
        )}
      </div>

      {uniqueVehicles.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>Vehicle profile</div>
          <div style={{ fontSize: 12.5, color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
            {uniqueVehicles.length === 1
              ? `${uniqueVehicles[0].fuel_efficiency_factor}x fuel efficiency · ${uniqueVehicles[0].acceleration_response}x acceleration response · ${uniqueVehicles[0].tank_capacity_liters} L tank`
              : `Across ${uniqueVehicles.length} vehicles with varying characteristics`
            }
          </div>
        </div>
      )}

      {uniqueRoutes.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 2 }}>Route profile</div>
          <div style={{ fontSize: 12.5, color: 'var(--color-text-secondary)' }}>
            {uniqueRoutes.length === 1
              ? `${uniqueRoutes[0].speed_limit_kmh} km/h speed limit · ${uniqueRoutes[0].route_type || 'urban'} route type`
              : `Across ${uniqueRoutes.length} routes with varying speed limits`
            }
          </div>
        </div>
      )}

      <div style={{
        marginTop: 10, paddingTop: 10,
        borderTop: '1px solid var(--color-accent)',
        fontSize: 12, color: 'var(--color-text-secondary)', lineHeight: 1.5,
      }}>
        <strong style={{ color: 'var(--color-text-primary)' }}>Expected simulated behavior</strong>
        <ul style={{ margin: '4px 0 0', paddingLeft: 18 }}>
          {dominantBehavior.includes('aggressive') && <li>More aggressive acceleration and driving variation</li>}
          {dominantBehavior.includes('eco') && <li>Smoother driving with reduced fuel consumption</li>}
          {dominantBehavior.includes('cautious' ) && <li>Conservative driving with gentler dynamics</li>}
          {dominantBehavior.includes('standard') && <li>Baseline driving behavior</li>}
          {dominantBehavior.length === 0 && <li>Standard driving behavior</li>}
          <li>Scenario-specific vehicle and driver telemetry</li>
        </ul>
        <div style={{ marginTop: 6, fontSize: 11.5, color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
          Telemetry generated by this scenario is synthetic simulation data produced from the configured driver, vehicle, and route characteristics.
        </div>
      </div>
    </div>
  );
}

function ScenariosTab({ scenarios, assignments, drivers, vehicles, routes, runsByScenario, onRefresh, onNotice, status, busy }) {
  const [form, setForm] = useState({ name: '', description: '', seed: 1, duration_seconds: 600, simulation_speed: 1, selected: [] });
  const [launchConfirm, setLaunchConfirm] = useState(null);

  const submit = useCallback(async () => {
    if (!form.name) { onNotice('Scenario name is required'); return; }
    setForm((f) => ({ ...f, saving: true }));
    try {
      const created = await digitalTwinApi.createScenario({
        name: form.name,
        description: form.description || undefined,
        seed: parseInt(form.seed, 10) || null,
        duration_seconds: parseInt(form.duration_seconds, 10) || null,
        simulation_speed: parseFloat(form.simulation_speed) || null,
      }, form.selected);
      onNotice(`Scenario ${created?.data?.scenario_id} created`);
      setForm({ name: '', description: '', seed: 1, duration_seconds: 600, simulation_speed: 1, selected: [] });
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Failed to create scenario');
    } finally {
      setForm((f) => ({ ...f, saving: false }));
    }
  }, [form, onRefresh, onNotice]);

  const toggleAssignment = useCallback((id) => {
    setForm((f) => ({
      ...f,
      selected: f.selected.includes(id) ? f.selected.filter((x) => x !== id) : [...f.selected, id],
    }));
  }, []);

  const activate = useCallback(async (id) => {
    try {
      await digitalTwinApi.activateScenario(id);
      onNotice('Scenario activated (Ready)');
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Activate failed');
    }
  }, [onRefresh, onNotice]);

  const launch = useCallback(async (id) => {
    try {
      await digitalTwinApi.launchScenario(id);
      onNotice('Scenario launched');
      setLaunchConfirm(null);
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Launch failed');
    }
  }, [onRefresh, onNotice]);

  const stop = useCallback(async (id) => {
    try {
      await digitalTwinApi.stopScenario(id);
      onNotice('Scenario stopped');
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Stop failed');
    }
  }, [onRefresh, onNotice]);

  const removeAssignmentFromScenario = useCallback(async (scenarioId, assignmentId) => {
    try {
      const scenario = scenarios.find((s) => s.scenario_id === scenarioId);
      if (!scenario) return;
      const currentIds = (scenario.assignment_ids || []).filter((id) => id !== assignmentId);
      await digitalTwinApi.setScenarioAssignments(scenarioId, currentIds);
      onNotice('Assignment removed from scenario');
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Failed to remove assignment');
    }
  }, [scenarios, onRefresh, onNotice]);

  const remove = useCallback(async (id) => {
    try {
      await digitalTwinApi.deleteScenario(id);
      onNotice('Scenario deleted');
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Delete failed');
    }
  }, [onRefresh, onNotice]);

  const inputStyle = {
    padding: '6px 10px', borderRadius: 6,
    border: '1px solid var(--color-border)',
    background: 'var(--color-bg)',
    color: 'var(--color-text-primary)',
    fontSize: 12.5, width: '100%',
  };

  const labelStyle = {
    fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)',
    textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4, display: 'block',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Launch confirmation dialog */}
      {launchConfirm && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(0,0,0,0.4)',
        }}>
          <div style={{
            padding: 24, borderRadius: 12, maxWidth: 420, width: '90%',
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border-light)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
          }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 8 }}>
              Launch scenario?
            </div>
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.6, marginBottom: 16 }}>
              This will stop the currently active Digital Twin runtime and start <strong>{launchConfirm.name}</strong> instead.
              Only one simulation runtime can be active at a time.
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button
                onClick={() => setLaunchConfirm(null)}
                style={{
                  padding: '7px 14px', borderRadius: 7, fontSize: 12.5, fontWeight: 600,
                  background: 'var(--color-surface)', color: 'var(--color-text-primary)',
                  border: '1px solid var(--color-border)', cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={() => launch(launchConfirm.scenario_id)}
                disabled={busy}
                style={{
                  padding: '7px 14px', borderRadius: 7, fontSize: 12.5, fontWeight: 600,
                  background: 'var(--color-accent)', color: '#fff',
                  border: '1px solid var(--color-accent)', cursor: busy ? 'wait' : 'pointer',
                }}
              >
                Launch scenario
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Section 1: Scenario Identity — Create Form */}
      <Card title="Scenario">
        <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)', marginBottom: 12 }}>
          Configure a simulation recipe for the Digital Twin.
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          <div>
            <label style={labelStyle}>Scenario name</label>
            <input placeholder="e.g. Aggressive Urban Test" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Description</label>
            <input placeholder="e.g. Simulates aggressive city driving" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} style={inputStyle} />
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginTop: 10 }}>
          <div>
            <label style={labelStyle}>Seed</label>
            <input type="number" value={form.seed} onChange={(e) => setForm({ ...form, seed: e.target.value })} style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Duration (seconds)</label>
            <input type="number" value={form.duration_seconds} onChange={(e) => setForm({ ...form, duration_seconds: e.target.value })} style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Simulation speed</label>
            <input type="number" step="0.1" value={form.simulation_speed} onChange={(e) => setForm({ ...form, simulation_speed: e.target.value })} style={inputStyle} />
          </div>
        </div>

        {/* Fleet composition — assignment picker */}
        <div style={{ marginTop: 14 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 6 }}>
            Scenario fleet
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 8 }}>
            Choose the driver, vehicle, and route combinations that will participate in this simulation.
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {assignments.map((a) => {
              const checked = form.selected.includes(a.assignment_id);
              const { driver, vehicle, route } = resolveAssignment(a, drivers, vehicles, routes);
              const label = [
                driver ? driverDisplayName(driver) : a.driver_id,
                vehicle ? `${vehicle.manufacturer} ${vehicle.model}` : a.vehicle_id,
                route ? `${route.origin}→${route.destination}` : a.route_id,
              ].join(' · ');
              return (
                <button
                  key={a.assignment_id}
                  onClick={() => toggleAssignment(a.assignment_id)}
                  style={{
                    padding: '5px 12px', borderRadius: 999, fontSize: 11.5, cursor: 'pointer',
                    background: checked ? 'var(--color-accent)' : 'var(--color-surface)',
                    color: checked ? '#fff' : 'var(--color-text-secondary)',
                    border: checked ? '1px solid var(--color-accent)' : '1px solid var(--color-border)',
                    maxWidth: '100%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}
                  title={label}
                >
                  {label}
                </button>
              );
            })}
            {!assignments.length && (
              <span style={{ fontSize: 12.5, color: 'var(--color-text-muted)' }}>
                No assignments exist yet. Create driver, vehicle, and route assignments on the Assignments tab first.
              </span>
            )}
          </div>
        </div>

        <button onClick={submit} disabled={form.saving} style={{
          marginTop: 14, display: 'flex', alignItems: 'center', gap: 6,
          padding: '8px 16px', borderRadius: 8,
          background: 'var(--color-accent)', color: '#fff',
          border: '1px solid var(--color-accent)', fontSize: 13, fontWeight: 600,
          cursor: form.saving ? 'wait' : 'pointer',
        }}>
          {form.saving ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Save size={14} />}
          Create scenario
        </button>
      </Card>

      {/* Scenario list */}
      {!scenarios.length && (
        <Card title="Scenarios">
          <EmptyRow text="No scenarios yet. Create one above to define a simulation recipe." />
        </Card>
      )}

      {scenarios.map((s) => {
        const runningThis = status?.running && status?.scenario_id === s.scenario_id;
        const scenarioAssignments = (s.assignment_ids || [])
          .map((aid) => assignments.find((a) => a.assignment_id === aid))
          .filter(Boolean);

        return (
          <div key={s.scenario_id} style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {/* Scenario header card */}
            <Card
              title={
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <span>{s.name}</span>
                  <Badge tone={STATUS_TONES[s.status] || 'neutral'}>{s.status}</Badge>
                  {runningThis && <Badge tone="green"><span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}><Zap size={10} />Live</span></Badge>}
                </div>
              }
              action={
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {s.status !== 'ready' && s.status !== 'running' && (
                    <button onClick={() => activate(s.scenario_id)} style={smallBtn('accent')}>Activate</button>
                  )}
                  {s.status === 'ready' && (
                    <button onClick={() => setLaunchConfirm({ scenario_id: s.scenario_id, name: s.name })} disabled={busy} style={smallBtn('accent')}><Play size={12} /> Launch</button>
                  )}
                  {runningThis && (
                    <button onClick={() => stop(s.scenario_id)} disabled={busy} style={smallBtn('neutral')}><Square size={12} /> Stop</button>
                  )}
                  <button onClick={() => remove(s.scenario_id)} title="Delete scenario" style={iconBtn}><Trash2 size={14} /></button>
                </div>
              }
            >
              {/* Active scenario banner */}
              {runningThis && (
                <div style={{
                  padding: '10px 14px', borderRadius: 8, marginBottom: 12,
                  background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.3)',
                  fontSize: 12.5, color: 'var(--color-green)', fontWeight: 500,
                  display: 'flex', alignItems: 'center', gap: 6,
                }}>
                  <Zap size={14} />
                  Active scenario — simulation is running
                </div>
              )}

              {/* Description */}
              {s.description && (
                <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 10, lineHeight: 1.5 }}>
                  {s.description}
                </div>
              )}

              {/* Scenario config */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 18px', fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 12 }}>
                <span>ID: {s.scenario_id}</span>
                <span>Seed: {s.seed ?? '—'}</span>
                <span>Duration: {s.duration_seconds != null ? `${s.duration_seconds}s` : '—'}</span>
                <span>Speed: {s.simulation_speed ?? 1}x</span>
              </div>

              {/* Launch warning */}
              {s.status === 'ready' && (
                <div style={{
                  padding: '8px 12px', borderRadius: 8, marginBottom: 12,
                  background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)',
                  fontSize: 12, color: 'var(--color-amber)', lineHeight: 1.5,
                  display: 'flex', alignItems: 'flex-start', gap: 6,
                }}>
                  <Info size={14} style={{ marginTop: 1, flexShrink: 0 }} />
                  <span>Launching this scenario replaces the currently active Digital Twin simulation. Only one simulation runtime can be active at a time.</span>
                </div>
              )}

              {/* Fleet composition */}
              <div style={{ marginBottom: 4 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Scenario fleet
                </div>
                {scenarioAssignments.length === 0 ? (
                  <div style={{
                    padding: '16px', borderRadius: 8, textAlign: 'center',
                    background: 'var(--color-bg)', border: '1px solid var(--color-border-light)',
                  }}>
                    <div style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 4 }}>
                      No vehicles are assigned to this scenario yet.
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                      Add a driver, vehicle, and route combination to define which fleet units will participate in the simulation.
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {scenarioAssignments.map((a) => (
                      <AssignmentCard
                        key={a.assignment_id}
                        assignment={a}
                        drivers={drivers}
                        vehicles={vehicles}
                        routes={routes}
                        onRemove={(aid) => removeAssignmentFromScenario(s.scenario_id, aid)}
                      />
                    ))}
                  </div>
                )}
              </div>
            </Card>

            {/* Simulation preview */}
            {scenarioAssignments.length > 0 && (
              <div style={{ marginTop: 10 }}>
                <ScenarioPreview
                  scenarioAssignments={scenarioAssignments}
                  drivers={drivers}
                  vehicles={vehicles}
                  routes={routes}
                />
              </div>
            )}

            {/* Run history */}
            {runsByScenario[s.scenario_id]?.length > 0 && (
              <div style={{
                marginTop: 10, padding: 14, borderRadius: 10,
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border-light)',
              }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
                  Simulation runs
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {runsByScenario[s.scenario_id].map((r) => (
                    <div key={r.run_id} style={{
                      display: 'grid', gridTemplateColumns: 'auto 1fr auto auto', gap: 10, alignItems: 'center',
                      padding: '6px 10px', borderRadius: 6,
                      background: 'var(--color-bg)', fontSize: 12,
                    }}>
                      <Badge tone={r.status === 'running' ? 'green' : r.status === 'completed' ? 'neutral' : r.status === 'stopped' ? 'amber' : 'neutral'}>
                        {r.status}
                      </Badge>
                      <span style={{ color: 'var(--color-text-muted)' }}>
                        Run {r.run_id.slice(0, 8)}{r.vehicles_active ? ` · ${r.vehicles_active} vehicle${r.vehicles_active !== 1 ? 's' : ''}` : ''}{r.trips_completed ? ` · ${r.trips_completed} trip${r.trips_completed !== 1 ? 's' : ''}` : ''}
                      </span>
                      {r.start_time && <span style={{ color: 'var(--color-text-muted)' }}>Started {r.start_time}</span>}
                      {r.end_time && <span style={{ color: 'var(--color-text-muted)' }}>Ended {r.end_time}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

const iconBtn = {
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  width: 28, height: 28, borderRadius: 6,
  border: '1px solid var(--color-border)',
  background: 'var(--color-surface)',
  color: 'var(--color-text-muted)', cursor: 'pointer',
};

const addBtn = {
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  width: 34, height: 32, borderRadius: 6,
  background: 'var(--color-accent)', color: '#fff',
  border: '1px solid var(--color-accent)', cursor: 'pointer',
};

function smallBtn(tone) {
  return {
    display: 'flex', alignItems: 'center', gap: 4,
    padding: '5px 12px', borderRadius: 7,
    fontSize: 12, fontWeight: 600, cursor: 'pointer',
    background: tone === 'accent' ? 'var(--color-accent)' : 'var(--color-surface)',
    color: tone === 'accent' ? '#fff' : 'var(--color-text-primary)',
    border: tone === 'accent' ? '1px solid var(--color-accent)' : '1px solid var(--color-border)',
  };
}

// ────────────────────────────────────────────────────────────
// Main page
// ────────────────────────────────────────────────────────────

export function DigitalTwinLabPage() {
  useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [status, setStatus] = useState(null);
  const [drivers, setDrivers] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [runsByScenario, setRunsByScenario] = useState({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const [st, dr, ve, ro, as, sc] = await Promise.all([
        digitalTwinApi.getStatus(),
        digitalTwinApi.listDrivers(),
        digitalTwinApi.listVehicles(),
        digitalTwinApi.listRoutes(),
        digitalTwinApi.listAssignments(),
        digitalTwinApi.listScenarios(),
      ]);
      setStatus(st?.data ?? null);
      setDrivers(dr?.data ?? []);
      setVehicles(ve?.data ?? []);
      setRoutes(ro?.data ?? []);
      setAssignments(as?.data ?? []);
      setScenarios(sc?.data ?? []);

      const runs = {};
      await Promise.all((sc?.data ?? []).map(async (s) => {
        try {
          const rr = await digitalTwinApi.listRuns(s.scenario_id);
          runs[s.scenario_id] = rr?.data ?? [];
        } catch {
          runs[s.scenario_id] = [];
        }
      }));
      setRunsByScenario(runs);
    } catch (err) {
      setError(err?.message || 'Failed to load Digital Twin data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await refresh();
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [refresh]);

  const flash = useCallback((msg) => {
    setNotice(msg);
    setTimeout(() => setNotice(null), 3000);
  }, []);

  const handleLaunch = useCallback(async () => {
    const ready = scenarios.find((s) => s.status === 'ready');
    if (!ready) { flash('No Ready scenario to launch. Activate one first.'); return; }
    setBusy(true);
    try {
      await digitalTwinApi.launchScenario(ready.scenario_id);
      flash('Scenario launched');
      await refresh();
    } catch (err) {
      flash(err?.detail || err?.message || 'Launch failed');
    } finally {
      setBusy(false);
    }
  }, [scenarios, refresh, flash]);

  const handleStop = useCallback(async () => {
    if (!status?.scenario_id) return;
    setBusy(true);
    try {
      await digitalTwinApi.stopScenario(status.scenario_id);
      flash('Simulation stopped');
      await refresh();
    } catch (err) {
      flash(err?.detail || err?.message || 'Stop failed');
    } finally {
      setBusy(false);
    }
  }, [status, refresh, flash]);

  const handleReset = useCallback(async () => {
    setBusy(true);
    try {
      await digitalTwinApi.reset();
      flash('Simulation reset to default fleet');
      await refresh();
    } catch (err) {
      flash(err?.detail || err?.message || 'Reset failed');
    } finally {
      setBusy(false);
    }
  }, [refresh, flash]);

  const fleetRefresh = useCallback(async () => {
    const [dr, ve, ro, as, sc] = await Promise.all([
      digitalTwinApi.listDrivers(),
      digitalTwinApi.listVehicles(),
      digitalTwinApi.listRoutes(),
      digitalTwinApi.listAssignments(),
      digitalTwinApi.listScenarios(),
    ]);
    setDrivers(dr?.data ?? []);
    setVehicles(ve?.data ?? []);
    setRoutes(ro?.data ?? []);
    setAssignments(as?.data ?? []);
    setScenarios(sc?.data ?? []);
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
          <FlaskConical size={20} strokeWidth={1.7} />
        </div>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 600, color: 'var(--color-text-primary)', margin: 0 }}>
            Digital Twin Lab
          </h2>
          <p style={{ fontSize: 12.5, color: 'var(--color-text-muted)', margin: '2px 0 0' }}>
            Simulated fleet configuration and scenario lifecycle (admin)
          </p>
        </div>
        {!loading && <StatusPill running={Boolean(status?.running)} />}
      </div>

      {error && (
        <div style={{
          padding: '10px 14px', borderRadius: 8, fontSize: 12.5, marginTop: 8,
          background: 'rgba(239,68,68,0.1)', color: 'var(--color-red)',
          border: '1px solid rgba(239,68,68,0.3)',
        }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><AlertCircle size={14} /> {error}</span>
        </div>
      )}

      {!loading && notice && (
        <div style={{
          padding: '8px 12px', borderRadius: 8, fontSize: 12.5, marginTop: 8,
          background: 'var(--color-accent-subtle)', color: 'var(--color-accent)',
          border: '1px solid var(--color-accent)',
        }}>
          {notice}
        </div>
      )}

      {/* Tabs */}
      <div style={{
        display: 'flex', gap: 4, marginTop: 20, marginBottom: 20,
        borderBottom: '1px solid var(--color-border-light)',
        overflowX: 'auto',
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
          {activeTab === 'overview' && (
            <OverviewTab
              status={status}
              onLaunch={handleLaunch}
              onStop={handleStop}
              onReset={handleReset}
              busy={busy}
            />
          )}
          {activeTab === 'fleet' && (
            <FleetTab
              drivers={drivers}
              vehicles={vehicles}
              routes={routes}
              onRefresh={fleetRefresh}
              notice={notice}
              onNotice={flash}
            />
          )}
          {activeTab === 'assignments' && (
            <AssignmentsTab
              assignments={assignments}
              drivers={drivers}
              vehicles={vehicles}
              routes={routes}
              onRefresh={fleetRefresh}
              onNotice={flash}
            />
          )}
          {activeTab === 'scenarios' && (
            <ScenariosTab
              scenarios={scenarios}
              assignments={assignments}
              drivers={drivers}
              vehicles={vehicles}
              routes={routes}
              runsByScenario={runsByScenario}
              onRefresh={fleetRefresh}
              onNotice={flash}
              status={status}
              busy={busy}
            />
          )}
        </>
      )}
    </div>
  );
}

export default DigitalTwinLabPage;
