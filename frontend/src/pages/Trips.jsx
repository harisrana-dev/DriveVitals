import { useCallback } from 'react';
import { useTripsFilters } from '../hooks/useTripsFilters';
import { useTripDrawer } from '../context/TripDrawerContext';
import { TripsKpis } from '../components/trips/TripsKpis';
import { TripsFilters } from '../components/trips/TripsFilters';
import { TripsTable } from '../components/trips/TripsTable';
import { TripDrawer } from '../components/trips/TripDrawer';
import { ConnectionBadge } from '../components/ui/ConnectionBadge';
import { OfflineState } from '../components/ui/OfflineState';
import { useLiveData } from '../context/LiveDataContext';

export function TripsPage() {
  const {
    trips,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    routeFilter,
    setRouteFilter,
    sortBy,
    setSortBy,
    sortAsc,
    toggleSort,
  } = useTripsFilters();

  const { selectedTrip, openDrawer, closeDrawer } = useTripDrawer();
  const { overallStatus } = useLiveData();

  const handleTripClick = useCallback((trip) => {
    openDrawer(trip);
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
            Trips
          </h1>
          <p
            style={{
              fontSize: 13,
              color: 'var(--color-text-secondary)',
            }}
          >
            Historical trip intelligence and route analytics
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
              Updated in real-time
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
          <TripsKpis />

          <TripsFilters
            search={search}
            onSearchChange={setSearch}
            statusFilter={statusFilter}
            onStatusChange={setStatusFilter}
            routeFilter={routeFilter}
            onRouteChange={setRouteFilter}
            sortBy={sortBy}
            onSortChange={setSortBy}
            sortAsc={sortAsc}
            onSortToggle={toggleSort}
          />

          <TripsTable
            trips={trips}
            onTripClick={handleTripClick}
            selectedTripId={selectedTrip?.id}
          />
        </>
      )}

      {selectedTrip && (
        <TripDrawer
          trip={selectedTrip}
          onClose={closeDrawer}
        />
      )}
    </div>
  );
}
