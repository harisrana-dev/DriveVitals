import { useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useLiveData } from '../context/LiveDataContext';
import { useVehicleDrawer } from '../context/VehicleDrawerContext';
import { useMaintenance, useMaintenanceFilters } from '../hooks/useMaintenance';
import { MaintenanceCommandHeader } from '../components/maintenance/MaintenanceCommandHeader';
import { MaintenanceKpiStrip } from '../components/maintenance/MaintenanceKpiStrip';
import { MaintenanceAttentionQueue } from '../components/maintenance/MaintenanceAttentionQueue';
import { MaintenanceIntelligence } from '../components/maintenance/MaintenanceIntelligence';
import { ServiceWorkQueue } from '../components/maintenance/ServiceWorkQueue';
import { MaintenanceHistory } from '../components/maintenance/MaintenanceHistory';
import { MaintenanceDrawer } from '../components/maintenance/MaintenanceDrawer';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';

/**
 * Maintenance page — fleet service command centre.
 *
 * IA: CommandHeader -> KPI strip + Attention Queue -> Fleet Maintenance
 * Intelligence (vehicle risk + workload + horizon + insights) -> Service
 * Work Queue (tabs + filters + table) -> Service History -> drawer.
 *
 * Filter state is lifted to this page (useMaintenanceFilters) so the KPI
 * strip, tabs, filters bar and table share one source of truth. The
 * drawer is opened via the `?vehicle=` deep link so the Alerts page can
 * navigate here directly.
 */
export function MaintenancePage() {
  const maintenanceApi = useMaintenance();
  const filtersApi = useMaintenanceFilters();
  const { hydrated, connectionStatus } = useLiveData();
  const { openDrawer: openVehicleDrawer } = useVehicleDrawer();
  const [searchParams, setSearchParams] = useSearchParams();
  const queueRef = useRef(null);

  const selectedVehicleId = searchParams.get('vehicle');

  const handleOpenDrawer = useCallback((vehicleId) => {
    setSearchParams({ vehicle: vehicleId }, { replace: true });
  }, [setSearchParams]);

  const handleCloseDrawer = useCallback(() => {
    setSearchParams({}, { replace: true });
  }, [setSearchParams]);

  const handleViewVehicleProfile = useCallback(
    (vehicleId) => {
      setSearchParams({}, { replace: true });
      openVehicleDrawer({ id: vehicleId });
    },
    [setSearchParams, openVehicleDrawer]
  );

  const scrollToQueue = useCallback(() => {
    queueRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, []);

  const handleTypeSelect = useCallback(
    (typeKey) => {
      filtersApi.setType(typeKey);
      scrollToQueue();
    },
    [filtersApi, scrollToQueue]
  );

  const handleViewQueue = useCallback(() => {
    filtersApi.resetFilters();
    scrollToQueue();
  }, [filtersApi, scrollToQueue]);

  if (!hydrated) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1400 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Skeleton style={{ height: 56, borderRadius: 12 }} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(148px, 1fr))', gap: 10 }}>
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} style={{ height: 92, borderRadius: 12 }} />
            ))}
          </div>
        </div>
        <Skeleton style={{ height: 240, borderRadius: 12 }} />
        <Skeleton style={{ height: 440, borderRadius: 12 }} />
      </div>
    );
  }

  const isEmpty = maintenanceApi.workItems.length === 0 && maintenanceApi.history.length === 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1400 }}>
      <MaintenanceCommandHeader />

      {connectionStatus === 'offline' && (
        <div
          style={{
            padding: '10px 14px',
            borderRadius: 10,
            background: 'var(--color-red-bg)',
            color: 'var(--color-red)',
            fontSize: 12,
          }}
        >
          Fleet connection is offline. Data shown is the last snapshot received.
        </div>
      )}

      {isEmpty ? (
        <EmptyState
          title="No maintenance data"
          description="No maintenance records are available from the backend yet."
        />
      ) : (
        <>
          <section style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <MaintenanceKpiStrip
              kpis={maintenanceApi.kpis}
              activeKey={filtersApi.activeKpi}
              onSelect={filtersApi.applyKpiPreset}
            />
            <MaintenanceAttentionQueue
              workItems={maintenanceApi.workItems}
              onOpenVehicle={handleOpenDrawer}
            />
          </section>

          <MaintenanceIntelligence
            vehicleRisk={maintenanceApi.vehicleRisk}
            workload={maintenanceApi.workload}
            horizon={maintenanceApi.horizon}
            insights={maintenanceApi.insights}
            onViewVehicle={handleOpenDrawer}
            onTypeSelect={handleTypeSelect}
            activeType={filtersApi.filters.type}
            onViewQueue={handleViewQueue}
          />

          <div ref={queueRef}>
            <ServiceWorkQueue
              filtersApi={filtersApi}
              onOpenVehicle={handleOpenDrawer}
            />
          </div>

          <MaintenanceHistory
            history={maintenanceApi.history}
            onOpenVehicle={handleOpenDrawer}
          />
        </>
      )}

      {selectedVehicleId && (
        <MaintenanceDrawer
          key={selectedVehicleId}
          vehicleId={selectedVehicleId}
          onClose={handleCloseDrawer}
          onViewVehicle={handleViewVehicleProfile}
        />
      )}
    </div>
  );
}
