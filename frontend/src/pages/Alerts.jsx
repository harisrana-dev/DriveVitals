import { useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAlerts, useAlertFilters } from '../hooks/useAlerts';
import { useLiveData } from '../context/LiveDataContext';
import { useVehicleDrawer } from '../context/VehicleDrawerContext';
import { CommandHeader } from '../components/alerts/CommandHeader';
import { AlertKpiStrip } from '../components/alerts/AlertKpiStrip';
import { CriticalIncidentQueue } from '../components/alerts/CriticalIncidentQueue';
import { FleetAlertIntelligence } from '../components/alerts/FleetAlertIntelligence';
import { LiveNowBand } from '../components/alerts/LiveNowBand';
import { AlertHistory } from '../components/alerts/AlertHistory';
import { AlertDrawer } from '../components/alerts/AlertDrawer';
import { DriverProfileDrawer } from '../components/drivers/DriverProfileDrawer';
import { TripDrawer } from '../components/trips/TripDrawer';

/**
 * Alerts page — fleet incident command centre.
 *
 * IA: CommandHeader -> Attention Required (KPI strip + critical queue)
 *   -> Fleet Alert Intelligence (vehicle risk + distribution + insights)
 *   -> Live Now band -> Alert History (tabs + filters + table) -> drawer.
 *
 * Comparison-oriented UX: opening a target drawer from the Alert Drawer
 * keeps the Alert Drawer visible side-by-side. All drawers use the unified
 * stacking model via drawerLayout.js.
 */
export function AlertsPage() {
  const alertsApi = useAlerts();
  const filtersApi = useAlertFilters();
  const { trips, acknowledgeAllPassive } = useLiveData();
  const { openDrawer: openVehicleDrawer } = useVehicleDrawer();
  const navigate = useNavigate();

  const [selectedKey, setSelectedKey] = useState(null);
  const [selectedDriverId, setSelectedDriverId] = useState(null);
  const [selectedTripId, setSelectedTripId] = useState(null);

  const hasAlertDrawer = !!selectedKey;

  const selectedIncident = useMemo(
    () => alertsApi.incidents.find((i) => i.key === selectedKey) || null,
    [alertsApi.incidents, selectedKey]
  );

  const tripForDrawer = useMemo(() => {
    if (!selectedTripId) return null;
    const raw = (Array.isArray(trips?.trips) ? trips.trips : []).find(
      (t) => t && t.trip_id === selectedTripId
    );
    return raw ? { ...raw, id: raw.trip_id } : null;
  }, [trips, selectedTripId]);

  const handleIncidentClick = useCallback((incident) => {
    setSelectedKey(incident.key);
  }, []);
  const handleCloseDrawer = useCallback(() => {
    setSelectedKey(null);
  }, []);

  const handleViewVehicle = useCallback(
    (vehicleId) => {
      openVehicleDrawer({ id: vehicleId }, hasAlertDrawer ? 1 : 0);
    },
    [openVehicleDrawer, hasAlertDrawer]
  );

  const handleViewDriver = useCallback(
    (driverId) => {
      setSelectedDriverId(driverId);
    },
    []
  );

  const handleViewTrip = useCallback(
    (tripId) => {
      setSelectedTripId(tripId);
    },
    []
  );

  const handleViewMaintenance = useCallback(
    (vehicleId) => {
      navigate(`/maintenance?vehicle=${encodeURIComponent(vehicleId || '')}`);
    },
    [navigate]
  );

  const handleCategorySelect = useCallback(
    (categoryKey) => filtersApi.setCategory(categoryKey),
    [filtersApi]
  );

  const alertDrawerDepth = hasAlertDrawer ? 0 : -1;
  const targetDrawerDepth = hasAlertDrawer ? 1 : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1400 }}>
      <CommandHeader />

      <section style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <AlertKpiStrip
          kpis={alertsApi.kpis}
          activeKey={filtersApi.activeKpi}
          onSelect={filtersApi.applyKpiPreset}
        />
        <CriticalIncidentQueue
          incidents={alertsApi.incidents}
          onIncidentClick={handleIncidentClick}
          selectedKey={selectedKey}
        />
      </section>

      <FleetAlertIntelligence
        vehicleRisk={alertsApi.vehicleRisk}
        categoryDist={alertsApi.categoryDist}
        severityDist={alertsApi.activeSeverityDist}
        activeTotal={alertsApi.kpis.active}
        activeCategory={filtersApi.filters.category}
        onCategorySelect={handleCategorySelect}
        onViewVehicle={handleViewVehicle}
        insights={alertsApi.insights}
      />

      <LiveNowBand />

      <AlertHistory
        filtersApi={filtersApi}
        onIncidentClick={handleIncidentClick}
        selectedKey={selectedKey}
        onAcknowledgeAllPassive={acknowledgeAllPassive}
      />

      {selectedIncident && (
        <AlertDrawer
          incident={selectedIncident}
          onClose={handleCloseDrawer}
          onViewVehicle={handleViewVehicle}
          onViewDriver={handleViewDriver}
          onViewTrip={handleViewTrip}
          onViewMaintenance={handleViewMaintenance}
          depth={alertDrawerDepth}
        />
      )}

      {selectedDriverId && (
        <DriverProfileDrawer
          key={selectedDriverId}
          driverId={selectedDriverId}
          onClose={() => setSelectedDriverId(null)}
          depth={targetDrawerDepth}
        />
      )}

      {selectedTripId && tripForDrawer && (
        <TripDrawer
          trip={tripForDrawer}
          onClose={() => setSelectedTripId(null)}
          depth={targetDrawerDepth}
        />
      )}
    </div>
  );
}
