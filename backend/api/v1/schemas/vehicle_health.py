from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from backend.analytics.vehicle_health.health_config import (
    DEFAULT_HEALTH_CONFIG,
    status_for_score,
)


def _status_for_score(score: float | None) -> str | None:
    """Map a persisted score to the canonical health status."""
    if score is None:
        return None
    return status_for_score(score, DEFAULT_HEALTH_CONFIG.status).value


class HealthReasonRead(BaseModel):
    """Structured health reason, matching the live WebSocket shape."""

    subsystem: str
    reason: str
    code: str = ""
    title: str = ""
    severity: str = "warning"
    summary: str = ""
    evidence: dict[str, object] | None = None
    impact: str | None = None
    recommendation: str | None = None


class VehicleHealthRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vehicle_id: str
    overall_health_score: float | None
    engine_health: float | None
    brake_health: float | None
    transmission_health: float | None
    cooling_health: float | None
    fuel_system_health: float | None
    overall_health_status: str | None = None
    engine_health_status: str | None = None
    brake_health_status: str | None = None
    transmission_health_status: str | None = None
    cooling_health_status: str | None = None
    fuel_system_health_status: str | None = None
    health_reasons: list[HealthReasonRead] = []
    last_updated: datetime

    @field_validator("health_reasons", mode="before")
    @classmethod
    def _coerce_reasons(cls, value):
        """Tolerate rows persisted before reasons were stored."""
        return value or []

    @model_validator(mode="after")
    def _derive_statuses(self) -> "VehicleHealthRead":
        """Derive statuses from scores using the canonical thresholds.

        The live health engine applies the same thresholds, so the REST
        representation and the live dashboard always agree.
        """
        self.overall_health_status = _status_for_score(self.overall_health_score)
        self.engine_health_status = _status_for_score(self.engine_health)
        self.brake_health_status = _status_for_score(self.brake_health)
        self.transmission_health_status = _status_for_score(self.transmission_health)
        self.cooling_health_status = _status_for_score(self.cooling_health)
        self.fuel_system_health_status = _status_for_score(self.fuel_system_health)
        return self
