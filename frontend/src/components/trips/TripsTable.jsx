import { memo, useMemo } from 'react';
import { Route, MapPin, Clock, Gauge, Fuel, Shield } from 'lucide-react';
import { TripRow } from './TripRow';

const COLUMNS = [
  { key: 'trip', label: 'Trip / Vehicle', icon: null },
  { key: 'driver', label: 'Driver', icon: null },
  { key: 'route', label: 'Route', icon: MapPin },
  { key: 'distance', label: 'Distance', icon: Route },
  { key: 'duration', label: 'Duration', icon: Clock },
  { key: 'speed', label: 'Avg Speed', icon: Gauge },
  { key: 'fuel', label: 'Fuel', icon: Fuel },
  { key: 'score', label: 'Safety', icon: Shield },
  { key: '', label: '', icon: null },
];

export const TripsTable = memo(function TripsTable({ trips, onTripClick, selectedTripId }) {
  return (
    <div
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 12,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '2fr 1.5fr 1fr 1fr 1fr 1fr 1fr 1fr 48px',
          alignItems: 'center',
          gap: 8,
          padding: '10px 16px',
          borderBottom: '1px solid var(--color-border)',
          fontSize: 11,
          fontWeight: 600,
          color: 'var(--color-text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        <span>Trip</span>
        <span>Driver</span>
        <span>Route</span>
        <span>Distance</span>
        <span>Duration</span>
        <span>Avg Speed</span>
        <span>Fuel</span>
        <span>Safety</span>
        <span />
      </div>
      <div
        style={{
          maxHeight: 480,
          overflowY: 'auto',
        }}
      >
        {trips.length === 0 ? (
          <div
            style={{
              padding: '40px 16px',
              textAlign: 'center',
              color: 'var(--color-text-muted)',
              fontSize: 13,
            }}
          >
            No trips completed yet. Trips will appear here as vehicles complete their routes.
          </div>
        ) : (
          trips.map((trip, i) => (
            <div key={trip.id} className={`fade-in stagger-${Math.min(i + 1, 6)}`}>
              <TripRow
                trip={trip}
                onClick={onTripClick}
                isSelected={selectedTripId === trip.id}
              />
            </div>
          ))
        )}
      </div>
    </div>
  );
});
