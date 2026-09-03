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

// ────────────────────────────────────────────────────────────
// Fleet tab
// ────────────────────────────────────────────────────────────

function FleetTab({ drivers, vehicles, routes, onRefresh, notice, onNotice }) {
  const [driverForm, setDriverForm] = useState({ driver_id: '', name: '', behavior_profile: 'eco' });
  const [vehicleForm, setVehicleForm] = useState({ vehicle_id: '', make: '', model: '' });
  const [routeForm, setRouteForm] = useState({ route_id: '', origin: '', destination: '', distance_km: 10 });
  const [saving, setSaving] = useState(false);

  const submitDriver = useCallback(async () => {
    if (!driverForm.driver_id || !driverForm.name) return;
    setSaving(true);
    try {
      await digitalTwinApi.createDriver({ ...driverForm, behavior_profile: driverForm.behavior_profile });
      onNotice('Driver created');
      setDriverForm({ driver_id: '', name: '', behavior_profile: 'eco' });
      await onRefresh();
    } catch (err) {
      onNotice(err?.detail || err?.message || 'Failed to create driver');
    } finally {
      setSaving(false);
    }
  }, [driverForm, onRefresh, onNotice]);

  const submitVehicle = useCallback(async () => {
    if (!vehicleForm.vehicle_id || !vehicleForm.make || !vehicleForm.model) return;
    setSaving(true);
    try {
      await digitalTwinApi.createVehicle(vehicleForm);
      onNotice('Vehicle created');
      setVehicleForm({ vehicle_id: '', make: '', model: '' });
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
      await digitalTwinApi.createRoute({ ...routeForm, distance_km: parseFloat(routeForm.distance_km) || 0 });
      onNotice('Route created');
      setRouteForm({ route_id: '', origin: '', destination: '', distance_km: 10 });
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
            cells: [v.vehicle_id, `${v.make} ${v.model}`, v.year || '—'],
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
          <input placeholder="Make" value={vehicleForm.make} onChange={(e) => setVehicleForm({ ...vehicleForm, make: e.target.value })} style={inputStyle} />
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
            cells: [d.driver_id, d.name || '—', d.behavior_profile || '—'],
          }))}
          columns="0.8fr 1.2fr 0.8fr"
          renderActions={({ id }) => (
            <button onClick={() => removeDriver(id)} title="Delete" style={iconBtn}>
              <Trash2 size={14} />
            </button>
          )}
        />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 8, marginTop: 12, alignItems: 'end' }}>
          <input placeholder="ID" value={driverForm.driver_id} onChange={(e) => setDriverForm({ ...driverForm, driver_id: e.target.value })} style={inputStyle} />
          <input placeholder="Name" value={driverForm.name} onChange={(e) => setDriverForm({ ...driverForm, name: e.target.value })} style={inputStyle} />
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
            cells: [r.route_id, `${r.origin} → ${r.destination}`, `${r.distance_km} km`],
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
          <input type="number" placeholder="Distance km" value={routeForm.distance_km} onChange={(e) => setRouteForm({ ...routeForm, distance_km: e.target.value })} style={inputStyle} />
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

  const driverLabel = (id) => drivers.find((d) => d.driver_id === id)?.name || id;
  const vehicleLabel = (id) => {
    const v = vehicles.find((x) => x.vehicle_id === id);
    return v ? `${v.make} ${v.model}` : id;
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
            {drivers.map((d) => <option key={d.driver_id} value={d.driver_id}>{d.driver_id} · {d.name || ''}</option>)}
          </select>
          <select value={form.vehicle_id} onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })} style={selectStyle}>
            <option value="">Vehicle…</option>
            {vehicles.map((v) => <option key={v.vehicle_id} value={v.vehicle_id}>{v.vehicle_id} · {v.make} {v.model}</option>)}
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

function ScenariosTab({ scenarios, assignments, runsByScenario, onRefresh, onNotice, status, busy }) {
  const [form, setForm] = useState({ name: '', description: '', seed: 1, duration_seconds: 600, simulation_speed: 1, selected: [] });

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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Card title="Create scenario">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
          <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={inputStyle} />
          <input placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} style={inputStyle} />
          <input type="number" placeholder="Seed" value={form.seed} onChange={(e) => setForm({ ...form, seed: e.target.value })} style={inputStyle} />
          <input type="number" placeholder="Duration (s)" value={form.duration_seconds} onChange={(e) => setForm({ ...form, duration_seconds: e.target.value })} style={inputStyle} />
          <input type="number" step="0.1" placeholder="Speed" value={form.simulation_speed} onChange={(e) => setForm({ ...form, simulation_speed: e.target.value })} style={inputStyle} />
        </div>

        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 6 }}>Assignments in this scenario</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {assignments.map((a) => {
              const checked = form.selected.includes(a.assignment_id);
              return (
                <button
                  key={a.assignment_id}
                  onClick={() => toggleAssignment(a.assignment_id)}
                  style={{
                    padding: '4px 10px', borderRadius: 999, fontSize: 11.5, cursor: 'pointer',
                    background: checked ? 'var(--color-accent)' : 'var(--color-surface)',
                    color: checked ? '#fff' : 'var(--color-text-secondary)',
                    border: checked ? '1px solid var(--color-accent)' : '1px solid var(--color-border)',
                  }}
                >
                  {a.assignment_id}
                </button>
              );
            })}
            {!assignments.length && <span style={{ fontSize: 12.5, color: 'var(--color-text-muted)' }}>No assignments yet.</span>}
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

      <Card title="Scenarios">
        {!scenarios.length && <EmptyRow text="No scenarios yet. Create one above." />}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {scenarios.map((s) => {
            const runningThis = status?.running && status?.scenario_id === s.scenario_id;
            return (
              <div key={s.scenario_id} style={{
                padding: 12, borderRadius: 10,
                border: '1px solid var(--color-border-light)',
                background: 'var(--color-bg)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--color-text-primary)' }}>{s.name}</span>
                      <Badge tone={STATUS_TONES[s.status] || 'neutral'}>{s.status}</Badge>
                      {runningThis && <Badge tone="green"><span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}><Zap size={10} />Live</span></Badge>}
                    </div>
                    {s.description && (
                      <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>{s.description}</div>
                    )}
                    <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', marginTop: 4 }}>
                      ID {s.scenario_id} · Seed {s.seed ?? '—'} · {s.duration_seconds ?? '∞'}s · Speed {s.simulation_speed ?? 1}
                    </div>
                    {s.assignment_ids?.length > 0 && (
                      <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', marginTop: 2 }}>
                        Assignments: {s.assignment_ids.join(', ')}
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {s.status !== 'ready' && s.status !== 'running' && (
                      <button onClick={() => activate(s.scenario_id)} style={smallBtn('accent')}>Activate</button>
                    )}
                    {s.status === 'ready' && (
                      <button onClick={() => launch(s.scenario_id)} disabled={busy} style={smallBtn('accent')}><Play size={12} /> Launch</button>
                    )}
                    {runningThis && (
                      <button onClick={() => stop(s.scenario_id)} disabled={busy} style={smallBtn('neutral')}><Square size={12} /> Stop</button>
                    )}
                    <button onClick={() => remove(s.scenario_id)} title="Delete" style={iconBtn}><Trash2 size={14} /></button>
                  </div>
                </div>

                {runsByScenario[s.scenario_id]?.length > 0 && (
                  <div style={{ marginTop: 10, borderTop: '1px solid var(--color-border-light)', paddingTop: 8 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
                      Runs
                    </div>
                    {runsByScenario[s.scenario_id].map((r) => (
                      <div key={r.run_id} style={{ display: 'flex', gap: 12, fontSize: 12, color: 'var(--color-text-secondary)' }}>
                        <span>{r.status}</span>
                        <span>{r.created_at || '—'}</span>
                        {r.started_at && <span>started {r.started_at}</span>}
                        {r.completed_at && <span>completed {r.completed_at}</span>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Card>
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
