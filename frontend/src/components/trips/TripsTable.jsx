import { memo } from 'react';
import { TripRow } from './TripRow';

export const TripsTable = memo(function TripsTable({
  trips,
  onTripClick,
  selectedTripId,
  loading = false,
  hasMore = false,
  onLoadMore,
  loadingMore = false,
  loadedCount,
  totalCount,
}) {
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
          gridTemplateColumns: '1.8fr 1.5fr 1.2fr 0.9fr 0.9fr 0.9fr 0.8fr 0.9fr 110px 44px',
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
        <span>Status</span>
        <span />
      </div>
      <div
        style={{
          maxHeight: 480,
          overflowY: 'auto',
        }}
      >
        {loading ? (
          <div
            style={{
              padding: '40px 16px',
              textAlign: 'center',
              color: 'var(--color-text-muted)',
              fontSize: 13,
            }}
          >
            Loading trips...
          </div>
        ) : trips.length === 0 ? (
          <div
            style={{
              padding: '40px 16px',
              textAlign: 'center',
              color: 'var(--color-text-muted)',
              fontSize: 13,
            }}
          >
            No trips match the current filters.
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

        {hasMore && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 10,
              padding: '12px 16px',
              borderTop: '1px solid var(--color-border)',
            }}
          >
            <button
              onClick={onLoadMore}
              disabled={loadingMore}
              style={{
                padding: '8px 18px',
                borderRadius: 8,
                border: '1px solid var(--color-border)',
                background: 'var(--color-surface-hover)',
                color: 'var(--color-text-primary)',
                fontSize: 13,
                fontWeight: 600,
                cursor: loadingMore ? 'default' : 'pointer',
                opacity: loadingMore ? 0.6 : 1,
                transition: 'all 0.15s ease',
              }}
            >
              {loadingMore ? 'Loading...' : 'Load more trips'}
            </button>
            {totalCount != null && loadedCount != null && (
              <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                {loadedCount} of {totalCount} loaded
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
});
