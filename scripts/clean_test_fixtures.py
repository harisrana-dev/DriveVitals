"""
Remove test-fixture data from the development runtime database.

The API test suite (`tests/api/conftest.py`) seeds American placeholder
fixtures into whatever database it is pointed at. If it ever ran against the
development runtime database, those ghost rows must be purged manually.

This script removes ONLY test-fixture rows:

    Drivers:    d-*
    Vehicles:   v-*
    Routes:     r-*
    Trips:      t-*  (and any trip referencing d-*/v-*/r-*)
    Telemetry:  referencing t-*/v-*
    Behaviour:  referencing t-*/d-*/v-*
    Alerts:     referencing t-*/d-*/v-*
    Statistics: d-*
    Health:     v-*
    Maintenance: v-*

Runtime fleet_config rows (D-0*, V-10*, R-0*) are preserved.

Safety:
    Refuses to run against any database whose name ends in '_test'.

Usage:
    python -m scripts.clean_test_fixtures
"""

import asyncio
import logging

from sqlalchemy import text

from backend.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clean_test_fixtures")

DELETE_PLAN = [
    (
        "behaviour_events",
        "trip_id LIKE 't-%' OR driver_id LIKE 'd-%' OR vehicle_id LIKE 'v-%'",
    ),
    (
        "telemetry_samples",
        "trip_id LIKE 't-%' OR vehicle_id LIKE 'v-%'",
    ),
    (
        "alerts",
        "vehicle_id LIKE 'v-%' OR driver_id LIKE 'd-%' OR trip_id LIKE 't-%'",
    ),
    ("driver_statistics", "driver_id LIKE 'd-%'"),
    ("maintenance_records", "vehicle_id LIKE 'v-%'"),
    ("vehicle_health", "vehicle_id LIKE 'v-%'"),
    ("vehicle_statistics", "vehicle_id LIKE 'v-%'"),
    (
        "trips",
        "trip_id LIKE 't-%' OR vehicle_id LIKE 'v-%' "
        "OR driver_id LIKE 'd-%' OR route_id LIKE 'r-%'",
    ),
    ("drivers", "driver_id LIKE 'd-%'"),
    ("vehicles", "vehicle_id LIKE 'v-%'"),
    ("routes", "route_id LIKE 'r-%'"),
]


async def clean() -> None:
    database_name = str(engine.url.database or "")

    if database_name.endswith("_test"):
        raise RuntimeError(
            f"Refusing to clean test database '{database_name}'. "
            "This tool targets the development runtime database."
        )

    logger.info("Targeting database: %s", database_name)

    async with engine.begin() as conn:
        for table, where in DELETE_PLAN:
            sql = f"DELETE FROM {table} WHERE {where}"
            result = await conn.execute(text(sql))
            logger.info("  %-22s removed %d row(s)", table, result.rowcount)


async def main() -> None:
    try:
        await clean()
        logger.info("Cleanup complete.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
