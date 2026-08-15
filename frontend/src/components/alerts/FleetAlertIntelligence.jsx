import { memo } from 'react';
import { AlertsSectionTitle } from './AlertsSectionTitle';
import { VehicleRiskPanel } from './VehicleRiskPanel';
import { AlertDistribution } from './AlertDistribution';
import { InsightsCallouts } from './InsightsCallouts';

/**
 * Fleet Alert Intelligence: vehicle risk, active-alert distribution and
 * derived operational insights. All figures come from the canonical
 * selectors; the distribution and risk panel consume the same active
 * population so they always reconcile.
 */
export const FleetAlertIntelligence = memo(function FleetAlertIntelligence({
  vehicleRisk,
  categoryDist,
  severityDist,
  activeTotal,
  activeCategory,
  onCategorySelect,
  onViewVehicle,
  insights,
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <AlertsSectionTitle title="Fleet Alert Intelligence" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, alignItems: 'start' }}>
        <VehicleRiskPanel vehicles={vehicleRisk} onViewVehicle={onViewVehicle} />
        <AlertDistribution
          categoryDist={categoryDist}
          severityDist={severityDist}
          activeTotal={activeTotal}
          activeCategory={activeCategory}
          onCategorySelect={onCategorySelect}
        />
      </div>
      <InsightsCallouts insights={insights} />
    </div>
  );
});
