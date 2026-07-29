import { useState, useCallback } from 'react';
import { VehicleHealthOverview } from '../components/vehicleHealth/VehicleHealthOverview';
import { HealthDistribution } from '../components/vehicleHealth/HealthDistribution';
import { VehicleHealthMatrix } from '../components/vehicleHealth/VehicleHealthMatrix';
import { VehicleHealthDrawer } from '../components/vehicleHealth/VehicleHealthDrawer';

export function VehicleHealthPage() {
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);

  const handleVehicleClick = useCallback((id) => {
    setSelectedVehicleId(id);
  }, []);

  const handleCloseDrawer = useCallback(() => {
    setSelectedVehicleId(null);
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
      <VehicleHealthOverview />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '300px 1fr',
          gap: 20,
          alignItems: 'start',
        }}
      >
        <HealthDistribution />
        <VehicleHealthMatrix onVehicleClick={handleVehicleClick} />
      </div>

      {selectedVehicleId && (
        <VehicleHealthDrawer
          vehicleId={selectedVehicleId}
          onClose={handleCloseDrawer}
        />
      )}
    </div>
  );
}
