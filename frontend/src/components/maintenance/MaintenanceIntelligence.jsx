import { memo } from 'react';
import { MaintenanceSectionTitle } from './MaintenanceSectionTitle';
import { VehicleMaintenanceRiskPanel } from './VehicleMaintenanceRiskPanel';
import { ServiceWorkloadPanel } from './ServiceWorkloadPanel';
import { MaintenanceHorizonPanel } from './MaintenanceHorizonPanel';
import { MaintenanceInsights } from './MaintenanceInsights';

/**
 * Fleet Maintenance Intelligence: vehicle risk, service workload and the
 * scheduled-due horizon. All figures come from the canonical selectors so
 * the panels always reconcile with the KPI strip and work queue. Clicking
 * a service type filters the queue to that type.
 */
export const MaintenanceIntelligence = memo(function MaintenanceIntelligence({
  vehicleRisk,
  workload,
  horizon,
  insights,
  onViewVehicle,
  onTypeSelect,
  activeType,
  onViewQueue,
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <MaintenanceSectionTitle title="Fleet Maintenance Intelligence" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, alignItems: 'start' }}>
        <VehicleMaintenanceRiskPanel vehicles={vehicleRisk} onOpenVehicle={onViewVehicle} />
        <ServiceWorkloadPanel
          workload={workload}
          onTypeSelect={onTypeSelect}
          activeType={activeType}
        />
      </div>
      <MaintenanceHorizonPanel horizon={horizon} onOpenAll={onViewQueue} />
      <MaintenanceInsights insights={insights} />
    </div>
  );
});
