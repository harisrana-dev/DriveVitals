import { memo } from 'react';
import { VehicleCard } from './VehicleCard';
import { Truck } from 'lucide-react';

export const VehicleGrid = memo(function VehicleGrid({ vehicles, onVehicleClick }) {
  if (!vehicles || vehicles.length === 0) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '64px 24px',
          color: 'var(--color-text-muted)',
          gap: 12,
        }}
      >
        <Truck size={32} strokeWidth={1.5} />
        <span style={{ fontSize: 14, fontWeight: 500 }}>
          No vehicles found
        </span>
        <span style={{ fontSize: 12 }}>
          Try adjusting your search or filters
        </span>
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 16,
      }}
      className="fleet-vehicle-grid"
    >
      {vehicles.map((vehicle, i) => (
        <VehicleCard
          key={vehicle.id}
          vehicle={vehicle}
          index={i}
          onClick={onVehicleClick}
        />
      ))}

      <style>{`
        @media (max-width: 1280px) {
          .fleet-vehicle-grid {
            grid-template-columns: repeat(2, 1fr) !important;
          }
        }
        @media (max-width: 768px) {
          .fleet-vehicle-grid {
            grid-template-columns: repeat(2, 1fr) !important;
          }
        }
        @media (max-width: 560px) {
          .fleet-vehicle-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
});
