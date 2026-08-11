import { memo, useCallback } from 'react';
import { useVehicleHealth } from '../../hooks/useVehicleHealth';
import { VehicleHealthCard } from './VehicleHealthCard';

export const VehicleHealthMatrix = memo(function VehicleHealthMatrix({ onVehicleClick, vehicles: vehiclesProp, noResultsMessage }) {
  const { vehicles: allVehicles } = useVehicleHealth();
  const vehicles = vehiclesProp ?? allVehicles;

  const handleClick = useCallback((id) => {
    onVehicleClick?.(id);
  }, [onVehicleClick]);

  if (!vehicles || vehicles.length === 0) {
    return (
      <div
        style={{
          padding: '40px 16px',
          textAlign: 'center',
          color: 'var(--color-text-muted)',
          fontSize: 13,
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 12,
        }}
      >
        {noResultsMessage || 'No vehicle health data available.'}
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 12,
      }}
    >
      {vehicles.map((v, i) => (
        <VehicleHealthCard
          key={v.id}
          vehicle={v}
          index={i}
          onClick={handleClick}
        />
      ))}
    </div>
  );
});
