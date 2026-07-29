import { useCallback } from 'react';
import { RefreshCw, Radio } from 'lucide-react';
import { useDashboardSocket } from '../hooks/useDashboardSocket';
import { FleetSummary } from '../components/fleet/FleetSummary';
import { FleetFilters } from '../components/fleet/FleetFilters';
import { VehicleGrid } from '../components/fleet/VehicleGrid';
import { FleetStatusRing } from '../components/fleet/FleetStatusRing';
import { useFleetFilters } from '../hooks/useFleetFilters';
import { useVehicleDrawer } from '../context/VehicleDrawerContext';

export function FleetPage() {
  useDashboardSocket();

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
            Updated just now
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
    </div>
  );
}
