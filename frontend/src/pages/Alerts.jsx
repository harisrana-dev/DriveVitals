import { useState, useCallback } from 'react';
import { AlertsOverview } from '../components/alerts/AlertsOverview';
import { AlertFilters } from '../components/alerts/AlertFilters';
import { LiveAlertFeed } from '../components/alerts/LiveAlertFeed';
import { AlertSummaryChart } from '../components/alerts/AlertSummaryChart';
import { MostActiveVehicles } from '../components/alerts/MostActiveVehicles';
import { CriticalIncidentQueue } from '../components/alerts/CriticalIncidentQueue';
import { AlertDistribution } from '../components/alerts/AlertDistribution';
import { AlertTimeline } from '../components/alerts/AlertTimeline';
import { DrivingEventsFeed } from '../components/alerts/DrivingEventsFeed';
import { AlertDrawer } from '../components/alerts/AlertDrawer';

export function AlertsPage() {
  const [selectedAlertId, setSelectedAlertId] = useState(null);
  const handleAlertClick = useCallback((alert) => { setSelectedAlertId(alert.id); }, []);
  const handleCloseDrawer = useCallback(() => { setSelectedAlertId(null); }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 1400 }}>
      <AlertsOverview />
      <AlertFilters />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 20, alignItems: 'start' }}>
        <LiveAlertFeed onAlertClick={handleAlertClick} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <AlertSummaryChart />
          <MostActiveVehicles />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <CriticalIncidentQueue />
        <AlertDistribution />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <DrivingEventsFeed />
        <AlertTimeline />
      </div>

      {selectedAlertId && <AlertDrawer alertId={selectedAlertId} onClose={handleCloseDrawer} />}
    </div>
  );
}
