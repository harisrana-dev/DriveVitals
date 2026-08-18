import logging
from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import NAMESPACE_OID, uuid4, uuid5

from sqlalchemy import select, update
import sqlalchemy as sa

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
        condition: str | None = None,
        category: str | None = None,
        evidence: dict | None = None,
        source: str = "alert_engine",
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
            acknowledged_at=None,
            condition=condition,
            category=category,
            message=message,
            evidence=evidence,
            source=source,
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
        condition: str | None = None,
        category: str | None = None,
        evidence: dict | None = None,
        source: str = "alert_engine",
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
                    condition=condition,
                    category=category,
                    message=message,
                    evidence=evidence,
                    last_triggered_at=created_at,
                )
            )
            await self._session.flush()
            # Refresh to get updated values
            await self._session.refresh(existing_row)
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
            last_triggered_at=created_at,
            resolved_at=None,
            acknowledged_at=None,
            condition=condition,
            category=category,
            message=message,
            evidence=evidence,
            source=source,
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
        if row.acknowledged_at is None:
            row.acknowledged_at = datetime.now(timezone.utc)
        if row.resolved_at is None and row.status != "resolved":
            row.status = "active"
        await self._session.flush()
        return row

    async def resolve(self, alert_id: str) -> Alert | None:
        """Manually resolve an open alert (idempotent)."""
        row = await self._session.get(Alert, alert_id)
        if row is None:
            return None
        row.acknowledged = True
        if row.acknowledged_at is None:
            row.acknowledged_at = datetime.now(timezone.utc)
        if row.status != "resolved":
            row.status = "resolved"
        if row.resolved_at is None:
            row.resolved_at = datetime.now(timezone.utc)
        await self._session.flush()
        return row

    async def resolve_stale(
        self,
        vehicle_id: str,
        categories: Sequence[str],
        active_alert_ids: Sequence[str],
    ) -> tuple[int, list[Alert]]:
        """Resolve open alerts whose condition is no longer active.

        Alerts are scoped by their canonical condition key (the generator's
        ``alert_id``). A stored alert is considered still-active when its
        stored id shares the scoped prefix with one of ``active_alert_ids``.
        Everything else in ``categories`` for the vehicle that is still open
        is marked resolved (history is preserved, the row is not deleted).
        
        Returns a tuple of (resolved_count, resolved_alerts).
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
        resolved_alerts: list[Alert] = []
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
            resolved_alerts.append(row)

        if resolved:
            await self._session.flush()
        return resolved, resolved_alerts

    async def resolve_stale_trip_alerts(
        self,
        stale_after_seconds: float,
    ) -> tuple[int, list[Alert]]:
        """Resolve active trip alerts that haven't been re-triggered within
        the staleness window.

        A trip alert is considered stale when:
        - alert_type is 'trip'
        - status is 'active' (resolved_at IS NULL)
        - last_triggered_at (or created_at if NULL) is older than now - stale_after_seconds

        This prevents trip alerts from remaining active indefinitely when:
        - The triggering trip completed
        - No subsequent trip re-triggered the condition
        - The vehicle is idle

        Returns a tuple of (resolved_count, resolved_alerts).
        """
        from sqlalchemy import case, func

        stale_threshold = func.now() - sa.text(f"interval '{int(stale_after_seconds)} seconds'")

        trigger_time = case(
            (Alert.last_triggered_at.isnot(None), Alert.last_triggered_at),
            else_=Alert.created_at,
        )

        result = await self._session.execute(
            select(Alert).where(
                Alert.alert_type == "trip",
                Alert.resolved_at.is_(None),
                trigger_time < stale_threshold,
            )
        )

        resolved_at = datetime.now(timezone.utc)
        resolved = 0
        resolved_alerts: list[Alert] = []
        for row in result.scalars():
            row.status = "resolved"
            row.resolved_at = resolved_at
            resolved += 1
            resolved_alerts.append(row)

        if resolved:
            await self._session.flush()
        return resolved, resolved_alerts
