import { useState, useCallback } from 'react';
import { RefreshCw, Truck } from 'lucide-react';
import { VehicleHealthOverview } from '../components/vehicleHealth/VehicleHealthOverview';
import { HealthDistribution } from '../components/vehicleHealth/HealthDistribution';
import { VehicleHealthMatrix } from '../components/vehicleHealth/VehicleHealthMatrix';
import { VehicleHealthDrawer } from '../components/vehicleHealth/VehicleHealthDrawer';
import { HealthFilters } from '../components/vehicleHealth/HealthFilters';
import { useVehicleHealthFilters } from '../hooks/useVehicleHealthFilters';
import { useLiveData } from '../context/LiveDataContext';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';

function SkeletonGrid() {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '300px 1fr',
        gap: 20,
        alignItems: 'start',
      }}
    >
      <Skeleton style={{ height: 300, borderRadius: 12 }} />
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: 12,
        }}
      >
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} style={{ height: 300, borderRadius: 12 }} />
        ))}
      </div>
    </div>
  );
}

export function VehicleHealthPage() {
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);
  const { vehicles: rawVehicles, connectionStatus, sync } = useLiveData();
  const {
    vehicles,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    minScore,
    setMinScore,
    maxScore,
    setMaxScore,
    sortBy,
    setSortBy,
    sortAsc,
    toggleSort,
    hasActiveFilters,
    reset,
  } = useVehicleHealthFilters();

  const handleVehicleClick = useCallback((id) => {
    setSelectedVehicleId(id);
  }, []);

  const handleCloseDrawer = useCallback(() => {
    setSelectedVehicleId(null);
  }, []);

  const loading = connectionStatus === 'connecting' && (rawVehicles || []).length === 0;
  const empty = !loading && (rawVehicles || []).length === 0;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 20,
        maxWidth: 1400,
      }}
    >
      <VehicleHealthOverview />

      {loading ? (
        <SkeletonGrid />
      ) : empty ? (
        <EmptyState
          title="No vehicles in the fleet"
          description="Add vehicles to the fleet to start monitoring their health."
          icon={<Truck size={28} />}
          action={
            connectionStatus === 'offline' ? (
              <button
                onClick={sync}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '8px 14px',
                  borderRadius: 8,
                  border: '1px solid var(--color-accent)',
                  background: 'transparent',
                  color: 'var(--color-accent)',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                <RefreshCw size={14} />
                Retry
              </button>
            ) : undefined
          }
        />
      ) : (
        <>
          <HealthFilters
            search={search}
            onSearchChange={setSearch}
            statusFilter={statusFilter}
            onStatusChange={setStatusFilter}
            minScore={minScore}
            onMinScoreChange={setMinScore}
            maxScore={maxScore}
            onMaxScoreChange={setMaxScore}
            sortBy={sortBy}
            onSortChange={setSortBy}
            sortAsc={sortAsc}
            onSortToggle={toggleSort}
            hasActiveFilters={hasActiveFilters}
            onReset={reset}
          />

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '300px 1fr',
              gap: 20,
              alignItems: 'start',
            }}
          >
            <HealthDistribution />
            <VehicleHealthMatrix
              onVehicleClick={handleVehicleClick}
              vehicles={vehicles}
              noResultsMessage="No vehicles match the current filters."
            />
          </div>
        </>
      )}

      {selectedVehicleId && (
        <VehicleHealthDrawer
          vehicleId={selectedVehicleId}
          onClose={handleCloseDrawer}
        />
      )}
    </div>
  );
}
