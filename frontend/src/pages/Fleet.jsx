import { useCallback } from 'react';
import { FleetSummary } from '../components/fleet/FleetSummary';
import { FleetFilters } from '../components/fleet/FleetFilters';
import { VehicleGrid } from '../components/fleet/VehicleGrid';
import { FleetStatusRing } from '../components/fleet/FleetStatusRing';
import { ConnectionBadge } from '../components/ui/ConnectionBadge';
import { OfflineState } from '../components/ui/OfflineState';
import { useFleetFilters } from '../hooks/useFleetFilters';
import { useVehicleDrawer } from '../context/VehicleDrawerContext';
import { useLiveData } from '../context/LiveDataContext';

export function FleetPage() {
  const {
    vehicles,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    sortBy,
    setSortBy,
    sortAsc,
    toggleSort,
  } = useFleetFilters();

  const { openDrawer } = useVehicleDrawer();
  const { overallStatus } = useLiveData();

  const handleVehicleClick = useCallback((vehicle) => {
    openDrawer(vehicle);
  }, [openDrawer]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 20,
        maxWidth: 1400,
      }}
    >
      <div
        className="fade-in"
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              marginBottom: 4,
            }}
          >
            Fleet
          </h1>
          <p
            style={{
              fontSize: 13,
              color: 'var(--color-text-secondary)',
            }}
          >
            Live vehicle management and operational status
          </p>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <ConnectionBadge status={overallStatus} />
          {overallStatus === 'live' && (
            <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
              Updated just now
            </span>
          )}
          {overallStatus === 'rest' && (
            <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
              Showing REST data
            </span>
          )}
        </div>
      </div>

      {overallStatus === 'offline' ? (
        <OfflineState />
      ) : (
        <>
          <FleetSummary />

          <FleetFilters
            search={search}
            onSearchChange={setSearch}
            statusFilter={statusFilter}
            onStatusChange={setStatusFilter}
            sortBy={sortBy}
            onSortChange={setSortBy}
            sortAsc={sortAsc}
            onSortToggle={toggleSort}
          />

          <FleetStatusRing />

          <VehicleGrid
            vehicles={vehicles}
            onVehicleClick={handleVehicleClick}
          />
        </>
      )}
    </div>
  );
}
