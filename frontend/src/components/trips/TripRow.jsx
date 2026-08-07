import { memo } from 'react';
import { ChevronRight, MapPin, Clock, Gauge, Fuel, Shield } from 'lucide-react';

export const TripRow = memo(function TripRow({ trip, onClick, isSelected }) {
  return (
    <div
      onClick={() => onClick(trip)}
      style={{
        display: 'grid',
        gridTemplateColumns: '2fr 1.5fr 1fr 1fr 1fr 1fr 1fr 1fr 48px',
        alignItems: 'center',
        gap: 8,
        padding: '10px 16px',
        borderBottom: '1px solid var(--color-border-light)',
        cursor: 'pointer',
        background: isSelected ? 'var(--color-accent-subtle)' : 'transparent',
        transition: 'background 0.1s ease',
        fontSize: 13,
      }}
      onMouseEnter={(e) => {
        if (!isSelected) e.currentTarget.style.background = 'var(--color-surface-hover)';
      }}
      onMouseLeave={(e) => {
        if (!isSelected) e.currentTarget.style.background = 'transparent';
      }}
    >
      <div style={{ minWidth: 0 }}>
        <div style={{ fontWeight: 500, color: 'var(--color-text-primary)', fontFamily: 'monospace', fontSize: 12 }}>
          {trip.id}
        </div>
        <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 1 }}>
          {trip.vehicleName}
        </div>
      </div>

      <div>
        <div style={{ color: 'var(--color-text-primary)', fontWeight: 500, fontSize: 13 }}>
          {trip.driverName}
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
          {trip.driverId}
        </div>
      </div>

      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--color-text-primary)', minWidth: 0 }}>
          <MapPin size={11} style={{ color: 'var(--color-text-muted)', flexShrink: 0 }} />
          <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {trip.routeName || trip.routeType}
          </span>
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {trip.routeName ? trip.routeType : trip.routeId}
        </div>
      </div>

      <div style={{ fontVariantNumeric: 'tabular-nums', color: 'var(--color-text-primary)' }}>
        {trip.distanceFormatted}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontVariantNumeric: 'tabular-nums', color: 'var(--color-text-primary)' }}>
        <Clock size={11} style={{ color: 'var(--color-text-muted)' }} />
        <span>{trip.durationFormatted}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontVariantNumeric: 'tabular-nums', color: 'var(--color-text-primary)' }}>
        <Gauge size={11} style={{ color: 'var(--color-text-muted)' }} />
        <span>{trip.averageSpeed > 0 ? trip.averageSpeed.toFixed(1) : '—'}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontVariantNumeric: 'tabular-nums', color: 'var(--color-text-primary)' }}>
        <Fuel size={11} style={{ color: 'var(--color-text-muted)' }} />
        <span>{trip.fuelFormatted}</span>
      </div>

      <div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <Shield size={12} style={{ color: trip.gradeColor }} />
          <span style={{ fontWeight: 600, color: trip.gradeColor }}>
            {trip.grade || '—'}
          </span>
          <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
            {trip.safetyScore > 0 ? `${Math.round(trip.safetyScore)}%` : '—'}
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', color: 'var(--color-text-muted)' }}>
        <ChevronRight size={14} />
      </div>
    </div>
  );
});
