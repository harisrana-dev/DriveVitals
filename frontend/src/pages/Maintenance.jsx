import { useState, useCallback } from 'react';
import { MaintenanceOverview } from '../components/maintenance/MaintenanceOverview';
import { MaintenanceDistribution } from '../components/maintenance/MaintenanceDistribution';
import { ServiceQueue } from '../components/maintenance/ServiceQueue';
import { UpcomingSchedule } from '../components/maintenance/UpcomingSchedule';
import { FleetMaintenanceCost } from '../components/maintenance/FleetMaintenanceCost';
import { ServiceHistory } from '../components/maintenance/ServiceHistory';
import { MaintenanceDrawer } from '../components/maintenance/MaintenanceDrawer';

export function MaintenancePage() {
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);
  const handleServiceClick = useCallback((item) => { setSelectedVehicleId(item.vehicleId); }, []);
  const handleCloseDrawer = useCallback(() => { setSelectedVehicleId(null); }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1400 }}>
      <MaintenanceOverview />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 20, alignItems: 'start' }}>
        <ServiceQueue onServiceClick={handleServiceClick} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <MaintenanceDistribution />
          <UpcomingSchedule />
          <FleetMaintenanceCost />
        </div>
      </div>

      <ServiceHistory />

      {selectedVehicleId && (
        <MaintenanceDrawer vehicleId={selectedVehicleId} onClose={handleCloseDrawer} />
      )}
    </div>
  );
}
