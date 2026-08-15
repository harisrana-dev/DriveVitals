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
 * One click = one context surface. Vehicle uses the global vehicle
 * drawer; driver and trip are rendered locally here (there is no global
 * driver drawer and no nested drawers).
 */
export function AlertsPage() {
  const alertsApi = useAlerts();
  const filtersApi = useAlertFilters();
  const { trips } = useLiveData();
  const { openDrawer: openVehicleDrawer } = useVehicleDrawer();
  const navigate = useNavigate();

  const [selectedKey, setSelectedKey] = useState(null);
  const [selectedDriverId, setSelectedDriverId] = useState(null);
  const [selectedTripId, setSelectedTripId] = useState(null);

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
      setSelectedKey(null);
      openVehicleDrawer({ id: vehicleId });
    },
    [openVehicleDrawer]
  );

  const handleViewDriver = useCallback(
    (driverId) => {
      setSelectedKey(null);
      setSelectedDriverId(driverId);
    },
    []
  );

  const handleViewTrip = useCallback(
    (tripId) => {
      setSelectedKey(null);
      setSelectedTripId(tripId);
    },
    []
  );

  const handleViewMaintenance = useCallback(
    (vehicleId) => {
      setSelectedKey(null);
      navigate(`/maintenance?vehicle=${encodeURIComponent(vehicleId || '')}`);
    },
    [navigate]
  );

  const handleCategorySelect = useCallback(
    (categoryKey) => filtersApi.setCategory(categoryKey),
    [filtersApi]
  );

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
      />

      {selectedIncident && (
        <AlertDrawer
          incident={selectedIncident}
          onClose={handleCloseDrawer}
          onViewVehicle={handleViewVehicle}
          onViewDriver={handleViewDriver}
          onViewTrip={handleViewTrip}
          onViewMaintenance={handleViewMaintenance}
        />
      )}

      {selectedDriverId && (
        <DriverProfileDrawer
          key={selectedDriverId}
          driverId={selectedDriverId}
          onClose={() => setSelectedDriverId(null)}
        />
      )}

      {selectedTripId && tripForDrawer && (
        <TripDrawer trip={tripForDrawer} onClose={() => setSelectedTripId(null)} />
      )}
    </div>
  );
}
