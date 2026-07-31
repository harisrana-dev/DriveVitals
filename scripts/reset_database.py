"""
Database reset utility for development.

Safely clears event/history tables while preserving reference data:

    Cleared:
        behaviour_events
        telemetry_samples
        trips
        vehicle_health

    Preserved:
        vehicles
        drivers
        routes
        driver_statistics
        vehicle_statistics
        alerts
        maintenance_records

Usage:
    python -m scripts.reset_database
"""

import asyncio
import logging

from sqlalchemy import text

from backend.db.session import async_session_factory, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reset_database")

DELETE_ORDER = [
    "behaviour_events",
    "telemetry_samples",
    "trips",
    "vehicle_health",
]


async def reset() -> None:
    logger.info("Resetting event/history tables...")

    async with async_session_factory() as session:
        for table in DELETE_ORDER:
            logger.info("  Clearing %s...", table)
            await session.execute(text(f"DELETE FROM {table}"))
        await session.commit()

    logger.info("Database reset complete.")
    logger.info("Preserved: vehicles, drivers, routes, driver_statistics, vehicle_statistics, alerts, maintenance_records")


async def main() -> None:
    try:
        await reset()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
