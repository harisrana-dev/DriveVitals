import logging
from datetime import datetime, timezone
from uuid import NAMESPACE_OID, uuid4, uuid5

from sqlalchemy import select, update

from backend.db.models.alert import Alert
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

ALERT_ID_MAX_LENGTH = 36


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

    async def upsert(
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
        """Idempotently persist one alert keyed by a stable identity.

        The stored alert_id is a deterministic, vehicle-scoped variant of the
        generator's canonical alert_id (e.g. ``trip_unsafe:v-101``), so the
        same logical alert re-emitted across simulation cycles resolves to the
        same row instead of violating the alerts primary key.

        - An existing open (unresolved) row is updated in place; ``acknowledged``
          and ``resolved_at`` are preserved.
        - A genuinely new occurrence that would collide with a resolved head is
          stored under a fresh unique alert_id.
        - Otherwise the scoped id is inserted as a new row.
        """
        created_at = created_at or datetime.now(timezone.utc)
        scoped = self._scope_alert_id(alert_id, vehicle_id)

        existing = await self._session.execute(
            select(Alert)
            .where(
                Alert.vehicle_id == vehicle_id,
                Alert.alert_id.like(f"{scoped}%"),
            )
            .order_by(Alert.created_at.desc())
            .limit(1)
        )
        existing_row = existing.scalar_one_or_none()

        if existing_row is not None and existing_row.resolved_at is None:
            await self._session.execute(
                update(Alert)
                .where(Alert.alert_id == existing_row.alert_id)
                .values(
                    severity=severity,
                    created_at=created_at,
                    driver_id=driver_id,
                    trip_id=trip_id,
                    status=status,
                )
            )
            await self._session.flush()
            return existing_row

        stored_id = (
            self._unique_alert_id(scoped)
            if existing_row is not None
            else scoped
        )
        alert = Alert(
            alert_id=stored_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            trip_id=trip_id,
            alert_type=alert_type,
            severity=severity,
            status=status,
            acknowledged=False,
            created_at=created_at,
            resolved_at=None,
        )
        self._session.add(alert)
        await self._session.flush()
        return alert

    @staticmethod
    def _scope_alert_id(canonical: str, vehicle_id: str) -> str:
        scoped = f"{canonical}:{vehicle_id}"
        if len(scoped) > ALERT_ID_MAX_LENGTH:
            return str(uuid5(NAMESPACE_OID, scoped))
        return scoped

    @staticmethod
    def _unique_alert_id(scoped: str) -> str:
        return f"{scoped[: ALERT_ID_MAX_LENGTH - 6]}-{uuid4().hex[:5]}"
