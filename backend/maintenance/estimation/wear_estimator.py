"""
Wear Estimator.

Minimal foundation / extension point for future predictive
maintenance work. It does NOT implement a real wear-prediction model
yet — it only defines a clean interface that could later be filled in
using telemetry patterns such as braking frequency, brake pressure,
distance travelled, and aggressive-driving indicators.

Kept intentionally small so it's obvious this is a placeholder for
future work, not a finished feature.
"""

from dataclasses import dataclass
from typing import Iterable

from maintenance.models.vehicle_condition import VehicleCondition
from telemetry.models.telemetry_sample import TelemetrySample


@dataclass
class WearEstimator:
    """
    Future extension point: given a vehicle's current condition and a
    stream of telemetry samples, estimate updated wear values.

    The current implementation is intentionally a no-op / trivial
    pass-through so the interface exists without pretending to be a
    real predictive model.
    """

    def estimate(
        self,
        condition: VehicleCondition,
        samples: Iterable[TelemetrySample],
    ) -> VehicleCondition:
        """
        Placeholder implementation: returns the condition unchanged.

        A future version might, for example, increment brake_wear_percent
        based on cumulative brake_pressure across `samples`, or
        tire_wear_percent based on distance travelled and speed
        variance. That logic is intentionally not implemented yet.
        """
        return condition