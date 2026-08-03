import logging
from datetime import datetime, timezone

from backend.db.models.alert import Alert
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class AlertRepository(BaseRepository):
    async def insert(
        self,
        alert_id: str,
        vehicle_id: str,
        alert_type: str,
        severity: str,
        message: str,
        created_at: datetime | None = None,
        driver_id: str | None = None,
        trip_id: str | None = None,
        status: str = "active",
    ) -> Alert:
        alert = Alert(
            alert_id=alert_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            trip_id=trip_id,
            alert_type=alert_type,
            severity=severity,
            status=status,
            acknowledged=False,
            created_at=created_at or datetime.now(timezone.utc),
            resolved_at=None,
        )
        self._session.add(alert)
        await self._session.flush()
        return alert
