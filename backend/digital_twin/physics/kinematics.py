"""Kinematics: pure motion bookkeeping -- speed, distance, odometer.

Never computes forces or decides acceleration (that's Dynamics'
responsibility); Kinematics only integrates a given acceleration into a
new speed and turns speed into distance travelled. Speed is always
clamped to be non-negative.
"""

from __future__ import annotations

from digital_twin.physics import physics_constants as const


class Kinematics:
    """Integrates acceleration into speed and speed into distance.

    Stateless: every method is a pure function of its arguments.
    """

    def update_speed_kmh(
        self,
        current_speed_kmh: float,
        acceleration_mps2: float,
        delta_time_seconds: float,
    ) -> float:
        """Integrate acceleration over one tick to obtain the new speed.

        Args:
            current_speed_kmh: Speed at the start of this tick.
            acceleration_mps2: Acceleration to apply this tick, in
                meters per second squared (from Dynamics).
            delta_time_seconds: Simulated seconds elapsed this tick.

        Returns:
            The new speed, in km/h. Never negative -- a deceleration
            large enough to imply reversing simply clamps to 0.0,
            since reverse motion is out of scope for this sprint.
        """
        current_speed_mps = current_speed_kmh * const.KMH_TO_MPS
        new_speed_mps = current_speed_mps + acceleration_mps2 * delta_time_seconds
        new_speed_mps = max(0.0, new_speed_mps)
        return new_speed_mps * const.MPS_TO_KMH

    def compute_average_speed_kmh(
        self, speed_before_kmh: float, speed_after_kmh: float
    ) -> float:
        """Compute the average speed over a tick from its endpoints.

        Args:
            speed_before_kmh: Speed at the start of the tick.
            speed_after_kmh: Speed at the end of the tick.

        Returns:
            The arithmetic mean of the two speeds, in km/h. Using the
            mean of start/end speed is a standard trapezoidal
            approximation for distance-over-a-tick, accurate as long
            as acceleration is roughly constant within a tick (true
            here, since Dynamics computes exactly one acceleration
            value per tick).
        """
        return (speed_before_kmh + speed_after_kmh) / 2.0

    def compute_distance_travelled_km(
        self, average_speed_kmh: float, delta_time_seconds: float
    ) -> float:
        """Compute distance travelled this tick from average speed.

        Args:
            average_speed_kmh: Average speed over the tick, in km/h.
            delta_time_seconds: Simulated seconds elapsed this tick.

        Returns:
            Distance travelled this tick, in kilometers. Always
            non-negative.
        """
        delta_time_hours = delta_time_seconds / 3600.0
        return max(0.0, average_speed_kmh) * delta_time_hours

    def update_odometer_km(self, current_odometer_km: float, distance_travelled_km: float) -> float:
        """Accumulate distance travelled onto the odometer.

        Args:
            current_odometer_km: Odometer reading before this tick.
            distance_travelled_km: Distance travelled this tick, in
                kilometers.

        Returns:
            The new, cumulative odometer reading, in kilometers.
        """
        return current_odometer_km + max(0.0, distance_travelled_km)