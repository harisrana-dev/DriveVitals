import { useCallback, useState } from 'react';
import { Search } from 'lucide-react';
import { useDriversFilters } from '../hooks/useDrivers';
import { DriverOverview } from '../components/drivers/DriverOverview';
import { DriverCard } from '../components/drivers/DriverCard';
import { DriverRanking } from '../components/drivers/DriverRanking';
import { DriverProfileDrawer } from '../components/drivers/DriverProfileDrawer';

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
];

export function DriversPage() {
  const {
    drivers,
    search,
    setSearch,
    statusFilter,
    setStatusFilter,
    riskFilter,
    setRiskFilter,
  } = useDriversFilters();

  const [selectedDriverId, setSelectedDriverId] = useState(null);

  const handleDriverClick = useCallback((driver) => {
    setSelectedDriverId(driver.id);
  }, []);

  const handleCloseDrawer = useCallback(() => {
    setSelectedDriverId(null);
  }, []);

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
          gridTemplateColumns: '1fr 300px',
          gap: 20,
          alignItems: 'start',
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: 12,
          }}
        >
          {drivers.length === 0 ? (
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

        <div
          style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 12,
            padding: 16,
          }}
        >
          <DriverRanking onDriverClick={handleDriverClick} />
        </div>
      </div>

      {selectedDriverId && (
        <DriverProfileDrawer
          driverId={selectedDriverId}
          onClose={handleCloseDrawer}
        />
      )}
    </div>
  );
}
