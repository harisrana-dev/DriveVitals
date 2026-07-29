import { useCallback } from 'react';
import { RefreshCw, Radio } from 'lucide-react';
import { useTripsSocket } from '../hooks/useTripsSocket';
import { useTripsFilters } from '../hooks/useTripsFilters';
import { useTripDrawer } from '../context/TripDrawerContext';
import { TripsKpis } from '../components/trips/TripsKpis';
import { TripsFilters } from '../components/trips/TripsFilters';
import { TripsTable } from '../components/trips/TripsTable';
import { TripDrawer } from '../components/trips/TripDrawer';

export function TripsPage() {
  useTripsSocket();

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
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 12,
              color: 'var(--color-text-muted)',
            }}
          >
            <Radio size={13} style={{ color: 'var(--color-green)' }} />
            <span>Live</span>
          </div>
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            Updated in real-time
          </span>
          <button
            aria-label="Refresh data"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 32,
              height: 32,
              borderRadius: 8,
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              color: 'var(--color-text-secondary)',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--color-surface-hover)';
              e.currentTarget.style.color = 'var(--color-text-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'var(--color-surface)';
              e.currentTarget.style.color = 'var(--color-text-secondary)';
            }}
          >
            <RefreshCw size={15} strokeWidth={1.8} />
          </button>
        </div>
      </div>

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

      {selectedTrip && (
        <TripDrawer
          trip={selectedTrip}
          onClose={closeDrawer}
        />
      )}
    </div>
  );
}
