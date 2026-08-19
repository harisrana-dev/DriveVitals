import { useCallback, useState } from 'react';
import { Search, RefreshCw, Users, Trophy } from 'lucide-react';
import { useDriversFilters } from '../hooks/useDrivers';
import { useLiveData } from '../context/LiveDataContext';
import { DriverOverview } from '../components/drivers/DriverOverview';
import { DriverCard } from '../components/drivers/DriverCard';
import { DriverLeaderboard } from '../components/drivers/DriverLeaderboard';
import { DriverProfileDrawer } from '../components/drivers/DriverProfileDrawer';
import { Skeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';

const statusOptions = [
  { value: '', label: 'All Drivers' },
  { value: 'active', label: 'Active' },
  { value: 'off_duty', label: 'Off Duty' },
  { value: 'offline', label: 'Offline' },
];

const riskOptions = [
  { value: '', label: 'All Risk Levels' },
  { value: 'low', label: 'Low Risk' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'high', label: 'High Risk' },
  { value: 'critical', label: 'Critical' },
  { value: 'unknown', label: 'No Score' },
];

const performanceOptions = [
  { value: '', label: 'All Performance' },
  { value: 'improving', label: 'Improving' },
  { value: 'stable', label: 'Stable' },
  { value: 'declining', label: 'Declining' },
  { value: 'no_score', label: 'No Score Yet' },
];

function SkeletonGrid() {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 12,
      }}
    >
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} style={{ height: 320, borderRadius: 12 }} />
      ))}
    </div>
  );
}

export function DriversPage() {
  const { connectionStatus, hydrated, sync } = useLiveData();
  const {
    drivers,
    totalCount,
    hasActiveFilters,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    riskFilter,
    setRiskFilter,
    performanceFilter,
    setPerformanceFilter,
  } = useDriversFilters();

  const [selectedDriverId, setSelectedDriverId] = useState(null);

  const handleDriverClick = useCallback((driver) => {
    setSelectedDriverId(driver.id);
  }, []);

  const handleCloseDrawer = useCallback(() => {
    setSelectedDriverId(null);
  }, []);

  const loading = !hydrated && connectionStatus === 'connecting' && totalCount === 0;
  const emptyFleet = hydrated && totalCount === 0 && !hasActiveFilters;
  const noResults = hydrated && drivers.length === 0 && (hasActiveFilters || totalCount > 0);

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
            Drivers
          </h1>
          <p
            style={{
              fontSize: 13,
              color: 'var(--color-text-secondary)',
            }}
          >
            Monitor driver performance, safety behaviour, and operational efficiency
          </p>
        </div>
      </div>

      <DriverOverview />

      {loading ? (
        <SkeletonGrid />
      ) : emptyFleet ? (
        <EmptyState
          title="No drivers in the fleet"
          description="Drivers will appear here once they are added to the fleet."
          icon={<Users size={28} />}
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
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              flexWrap: 'wrap',
            }}
          >
            <div
              style={{
                position: 'relative',
                flex: '1 1 240px',
                minWidth: 180,
              }}
            >
              <Search
                size={14}
                style={{
                  position: 'absolute',
                  left: 12,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--color-text-muted)',
                  pointerEvents: 'none',
                }}
              />
              <input
                type="text"
                placeholder="Search drivers, vehicles..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px 8px 34px',
                  borderRadius: 8,
                  border: '1px solid var(--color-border)',
                  background: 'var(--color-surface)',
                  color: 'var(--color-text-primary)',
                  fontSize: 13,
                  outline: 'none',
                  transition: 'border-color 0.15s ease',
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-accent)'; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: 8,
                border: '1px solid var(--color-border)',
                background: 'var(--color-surface)',
                color: 'var(--color-text-primary)',
                fontSize: 13,
                outline: 'none',
                cursor: 'pointer',
                minWidth: 120,
                transition: 'border-color 0.15s ease',
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-accent)'; }}
              onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
            >
              {statusOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>

            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: 8,
                border: '1px solid var(--color-border)',
                background: 'var(--color-surface)',
                color: 'var(--color-text-primary)',
                fontSize: 13,
                outline: 'none',
                cursor: 'pointer',
                minWidth: 130,
                transition: 'border-color 0.15s ease',
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-accent)'; }}
              onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
            >
              {riskOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>

            <select
              value={performanceFilter}
              onChange={(e) => setPerformanceFilter(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: 8,
                border: '1px solid var(--color-border)',
                background: 'var(--color-surface)',
                color: 'var(--color-text-primary)',
                fontSize: 13,
                outline: 'none',
                cursor: 'pointer',
                minWidth: 130,
                transition: 'border-color 0.15s ease',
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--color-accent)'; }}
              onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
            >
              {performanceOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>

            <span
              style={{
                fontSize: 12,
                color: 'var(--color-text-muted)',
                marginLeft: 'auto',
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {drivers.length} driver{drivers.length !== 1 ? 's' : ''}
            </span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: 12,
            }}
          >
            {noResults ? (
              <div
                style={{
                  gridColumn: '1 / -1',
                  padding: '40px 16px',
                  textAlign: 'center',
                  color: 'var(--color-text-muted)',
                  fontSize: 13,
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 12,
                }}
              >
                No drivers match the current filters.
              </div>
            ) : (
              drivers.map((driver, i) => (
                <DriverCard
                  key={driver.id}
                  driver={driver}
                  onClick={handleDriverClick}
                  index={i}
                />
              ))
            )}
          </div>

          {!noResults && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <Trophy size={16} style={{ color: 'var(--color-amber)' }} />
                <h2
                  style={{
                    fontSize: 15,
                    fontWeight: 600,
                    color: 'var(--color-text-primary)',
                  }}
                >
                  Fleet Leaderboard
                </h2>
              </div>
              <DriverLeaderboard drivers={drivers} onDriverClick={handleDriverClick} />
            </div>
          )}
        </>
      )}

      {selectedDriverId && (
        <DriverProfileDrawer
          key={selectedDriverId}
          driverId={selectedDriverId}
          onClose={handleCloseDrawer}
        />
      )}
    </div>
  );
}
