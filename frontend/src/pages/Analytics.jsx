import { useAnalytics } from '../hooks/useAnalytics';
import { useLiveData } from '../context/useLiveData';
import { AnalyticsCommandHeader } from '../components/analytics/AnalyticsCommandHeader';
import { AnalyticsKpiStrip } from '../components/analytics/AnalyticsKpiStrip';
import { FleetPerformance } from '../components/analytics/FleetPerformance';
import { DriverIntelligence } from '../components/analytics/DriverIntelligence';
import { VehicleFuelAnalytics } from '../components/analytics/VehicleFuelAnalytics';
import { TripAnalytics } from '../components/analytics/TripAnalytics';
import { SafetyAnalysis } from '../components/analytics/SafetyAnalysis';
import { AnalyticsInsights } from '../components/analytics/AnalyticsInsights';
import { Spinner } from '../components/ui/Spinner';

export function AnalyticsPage() {
  const { vehicles, drivers } = useLiveData();

  const {
    range,
    setRange,
    customStart,
    setCustomStart,
    customEnd,
    setCustomEnd,
    vehicleFilter,
    setVehicleFilter,
    driverFilter,
    setDriverFilter,
    selectedDriverId,
    setSelectedDriverId,
    summary,
    fleetTrend,
    driverRanking,
    driverTrend,
    vehicleAnalytics,
    tripSummary,
    eventBreakdown,
    eventTrend,
    insights,
    loading,
    refresh,
    presets,
  } = useAnalytics();

  if (loading && !summary) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '60vh',
      }}>
        <div style={{ textAlign: 'center' }}>
          <Spinner size="lg" />
          <div style={{ marginTop: 12, fontSize: 13, color: 'var(--color-text-muted)' }}>
            Loading analytics data...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 1400 }}>
      <AnalyticsCommandHeader
        range={range}
        setRange={setRange}
        customStart={customStart}
        setCustomStart={setCustomStart}
        customEnd={customEnd}
        setCustomEnd={setCustomEnd}
        vehicleFilter={vehicleFilter}
        setVehicleFilter={setVehicleFilter}
        driverFilter={driverFilter}
        setDriverFilter={setDriverFilter}
        vehicles={vehicles}
        drivers={drivers}
        loading={loading}
        onRefresh={refresh}
        presets={presets}
      />

      <AnalyticsKpiStrip kpis={summary?.kpis} />

      <FleetPerformance fleetTrend={fleetTrend} />

      <DriverIntelligence
        driverRanking={driverRanking}
        driverTrend={driverTrend}
        selectedDriverId={selectedDriverId}
        onSelectDriver={setSelectedDriverId}
      />

      <VehicleFuelAnalytics vehicleAnalytics={vehicleAnalytics} />

      <TripAnalytics tripSummary={tripSummary} />

      <SafetyAnalysis
        eventBreakdown={eventBreakdown}
        eventTrend={eventTrend}
      />

      <AnalyticsInsights insights={insights} />
    </div>
  );
}
