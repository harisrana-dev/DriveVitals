import { useCallback } from 'react';
import { useTripsFilters } from '../hooks/useTripsFilters';
import { useTripDrawer } from '../context/TripDrawerContext';
import { useLiveData } from '../context/LiveDataContext';
import { TripsKpis } from '../components/trips/TripsKpis';
import { TripsFilters } from '../components/trips/TripsFilters';
import { TripsTable } from '../components/trips/TripsTable';
import { ActiveTripsList } from '../components/trips/ActiveTripsList';
import { TripDrawer } from '../components/trips/TripDrawer';

const TRIPS_CONNECTION_META = {
  live: { label: 'Live', color: 'var(--color-green)', bg: 'var(--color-green-bg)' },
  connecting: { label: 'Connecting…', color: 'var(--color-amber)', bg: 'var(--color-amber-bg)' },
  offline: { label: 'Offline', color: 'var(--color-red)', bg: 'var(--color-red-bg)' },
};

function ConnectionIndicator({ state }) {
  const meta = TRIPS_CONNECTION_META[state] || TRIPS_CONNECTION_META.offline;
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '4px 10px',
        borderRadius: 20,
        background: meta.bg,
        color: meta.color,
        fontSize: 11,
        fontWeight: 600,
        whiteSpace: 'nowrap',
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: meta.color,
          flexShrink: 0,
        }}
      />
      {meta.label}
    </span>
  );
}

function SectionHeader({ title, subtitle, count }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <h2
          style={{
            fontSize: 15,
            fontWeight: 600,
            color: 'var(--color-text-primary)',
          }}
        >
          {title}
        </h2>
        {count != null && (
          <span
            style={{
              fontSize: 12,
              color: 'var(--color-text-muted)',
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {count}
          </span>
        )}
      </div>
      {subtitle && (
        <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
          {subtitle}
        </span>
      )}
    </div>
  );
}

export function TripsPage() {
  const {
    activeTrips,
    historicalTrips,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    routeFilter,
    setRouteFilter,
    driverFilter,
    setDriverFilter,
    driverOptions,
    vehicleFilter,
    setVehicleFilter,
    vehicleOptions,
    gradeFilter,
    setGradeFilter,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
    sortBy,
    setSortBy,
    sortAsc,
    toggleSort,
    resetFilters,
    loadMoreTrips,
    retryTrips,
    summary,
    historyCount,
    historyLoaded,
    historyError,
    historyLoading,
    historyLoadingMore,
    historyHasMore,
  } = useTripsFilters();

  const { selectedTrip, openDrawer, closeDrawer } = useTripDrawer();
  const { tripsConnectionState } = useLiveData();

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
            Live trip tracking, historical trip intelligence and route analytics
          </p>
        </div>
        <ConnectionIndicator state={tripsConnectionState} />
      </div>

      <TripsKpis summary={summary} />

      <TripsFilters
        search={search}
        onSearchChange={setSearch}
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
        routeFilter={routeFilter}
        onRouteChange={setRouteFilter}
        driverFilter={driverFilter}
        onDriverChange={setDriverFilter}
        driverOptions={driverOptions}
        vehicleFilter={vehicleFilter}
        onVehicleChange={setVehicleFilter}
        vehicleOptions={vehicleOptions}
        gradeFilter={gradeFilter}
        onGradeChange={setGradeFilter}
        dateFrom={dateFrom}
        onDateFromChange={setDateFrom}
        dateTo={dateTo}
        onDateToChange={setDateTo}
        onReset={resetFilters}
        sortBy={sortBy}
        onSortChange={setSortBy}
        sortAsc={sortAsc}
        onSortToggle={toggleSort}
      />

      <div
        className="fade-in stagger-3"
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
        }}
      >
        <SectionHeader
          title="Active Trips"
          subtitle="Real-time updates via live stream"
          count={activeTrips.length}
        />
        <ActiveTripsList
          trips={activeTrips}
          onTripClick={handleTripClick}
          selectedTripId={selectedTrip?.id}
        />
        {activeTrips.length === 0 && (
          <div
            style={{
              padding: '28px 16px',
              textAlign: 'center',
              color: 'var(--color-text-muted)',
              fontSize: 13,
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 12,
            }}
          >
            No vehicles are currently on a trip. Active trips will appear here in real time.
          </div>
        )}
      </div>

      <div
        className="fade-in stagger-4"
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
        }}
      >
        <SectionHeader
          title="Trip History"
          subtitle="Completed and aborted trips with full analytics"
          count={historyCount}
        />
        {historyError && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 10,
              padding: '10px 16px',
              borderRadius: 8,
              background: 'var(--color-red-bg)',
              color: 'var(--color-red)',
              fontSize: 13,
            }}
          >
            <span>Failed to load trips. Showing the live trip stream instead.</span>
            <button
              onClick={retryTrips}
              style={{
                padding: '4px 12px',
                borderRadius: 6,
                border: '1px solid var(--color-red)',
                background: 'transparent',
                color: 'var(--color-red)',
                fontSize: 12,
                cursor: 'pointer',
              }}
            >
              Retry
            </button>
          </div>
        )}
        <TripsTable
          trips={historicalTrips}
          onTripClick={handleTripClick}
          selectedTripId={selectedTrip?.id}
          loading={historyLoading}
          hasMore={historyHasMore}
          onLoadMore={loadMoreTrips}
          loadingMore={historyLoadingMore}
          loadedCount={historyLoaded}
          totalCount={historyCount}
        />
      </div>

      {selectedTrip && (
        <TripDrawer
          trip={selectedTrip}
          onClose={closeDrawer}
        />
      )}
    </div>
  );
}
