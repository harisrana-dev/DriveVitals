import logging
from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import NAMESPACE_OID, uuid4, uuid5

from sqlalchemy import select, update

from backend.db.models.alert import Alert
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

ALERT_ID_MAX_LENGTH = 36

# Stored alert ids are the scoped id (``canonical:vehicle``) or a truncated
# ``scoped[:30]-suffix`` form when a resolved head collides. Truncating to 30
# chars keeps both forms comparable for stale-resolution matching.
ALERT_ID_MATCH_PREFIX = 30


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

        - An existing open (unresolved) row is updated in place; ``created_at``,
          ``acknowledged`` and ``resolved_at`` are preserved.
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

    async def acknowledge(self, alert_id: str) -> Alert | None:
        """Mark an alert as acknowledged, preserving its lifecycle state."""
        row = await self._session.get(Alert, alert_id)
        if row is None:
            return None
        row.acknowledged = True
        if row.resolved_at is None and row.status != "resolved":
            row.status = "active"
        await self._session.flush()
        return row

    async def resolve(self, alert_id: str) -> Alert | None:
        """Manually resolve an open alert."""
        row = await self._session.get(Alert, alert_id)
        if row is None:
            return None
        row.acknowledged = True
        row.status = "resolved"
        row.resolved_at = datetime.now(timezone.utc)
        await self._session.flush()
        return row

    async def resolve_stale(
        self,
        vehicle_id: str,
        categories: Sequence[str],
        active_alert_ids: Sequence[str],
    ) -> int:
        """Resolve open alerts whose condition is no longer active.

        Alerts are scoped by their canonical condition key (the generator's
        ``alert_id``). A stored alert is considered still-active when its
        stored id shares the scoped prefix with one of ``active_alert_ids``.
        Everything else in ``categories`` for the vehicle that is still open
        is marked resolved (history is preserved, the row is not deleted).
        """
        active_scoped = {
            self._scope_alert_id(alert_id, vehicle_id)
            for alert_id in active_alert_ids
        }

        result = await self._session.execute(
            select(Alert).where(
                Alert.vehicle_id == vehicle_id,
                Alert.alert_type.in_(categories),
                Alert.resolved_at.is_(None),
            )
        )

        resolved_at = datetime.now(timezone.utc)
        resolved = 0
        for row in result.scalars():
            stored = row.alert_id
            active = False
            for scoped in active_scoped:
                if (
                    stored == scoped
                    or stored.startswith(f"{scoped[:ALERT_ID_MATCH_PREFIX]}-")
                ):
                    active = True
                    break
            if active:
                continue
            row.status = "resolved"
            row.resolved_at = resolved_at
            resolved += 1

        if resolved:
            await self._session.flush()
        return resolved
