"""Quick data audit for analytics planning."""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError(
            "POSTGRES_PASSWORD environment variable is not set. "
            "Copy .env.example to .env and configure your database credentials."
        )
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "drivevitals_dev")
    dsn = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
    
    engine = create_async_engine(dsn, echo=False)
    
    async with engine.begin() as conn:
        tables = [
            "vehicles", "drivers", "trips", "behaviour_events",
            "alerts", "vehicle_health", "driver_statistics",
            "maintenance_records", "telemetry_samples"
        ]

        print("=== ROW COUNTS ===")
        for t in tables:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {t}"))
            count = result.scalar()
            print(f"  {t}: {count}")

        print("\n=== TRIP STATUSES ===")
        result = await conn.execute(text("SELECT status, COUNT(*) FROM trips GROUP BY status"))
        for row in result:
            print(f"  {row[0]}: {row[1]}")

        print("\n=== TRIP DATE RANGE (completed) ===")
        result = await conn.execute(text("SELECT MIN(start_time), MAX(end_time) FROM trips WHERE status = 'completed'"))
        r = result.first()
        print(f"  Earliest: {r[0]}")
        print(f"  Latest: {r[1]}")

        print("\n=== EVENT TYPES ===")
        result = await conn.execute(text("SELECT event_type, COUNT(*) FROM behaviour_events GROUP BY event_type"))
        for row in result:
            print(f"  {row[0]}: {row[1]}")

        print("\n=== EVENT SEVERITIES ===")
        result = await conn.execute(text("SELECT severity, COUNT(*) FROM behaviour_events GROUP BY severity"))
        for row in result:
            print(f"  {row[0]}: {row[1]}")

        print("\n=== DRIVER STATISTICS SAMPLE ===")
        result = await conn.execute(text("SELECT driver_id, total_trips, safety_score, fuel_efficiency, speeding_events, harsh_braking_events FROM driver_statistics LIMIT 5"))
        for row in result:
            print(f"  {row}")

        print("\n=== VEHICLE HEALTH SAMPLE ===")
        result = await conn.execute(text("SELECT vehicle_id, overall_health_score, engine_health, brake_health FROM vehicle_health LIMIT 5"))
        for row in result:
            print(f"  {row}")

        print("\n=== VEHICLE STATISTICS ===")
        result = await conn.execute(text("SELECT vehicle_id, trip_count, total_distance_km, average_fuel_efficiency, lifetime_health_score FROM vehicle_statistics LIMIT 5"))
        for row in result:
            print(f"  {row}")

        print("\n=== TRIP SCORES (completed) ===")
        result = await conn.execute(text("SELECT COUNT(*), AVG(trip_score), AVG(distance_km), AVG(fuel_used_liters) FROM trips WHERE status = 'completed'"))
        r = result.first()
        print(f"  count={r[0]}, avg_score={r[1]}, avg_distance={r[2]}, avg_fuel={r[3]}")

        print("\n=== ALERTS BY TYPE ===")
        result = await conn.execute(text("SELECT alert_type, COUNT(*) FROM alerts GROUP BY alert_type"))
        for row in result:
            print(f"  {row[0]}: {row[1]}")

        print("\n=== MAINTENANCE BY STATUS ===")
        result = await conn.execute(text("SELECT status, COUNT(*) FROM maintenance_records GROUP BY status"))
        for row in result:
            print(f"  {row[0]}: {row[1]}")

        print("\n=== BEHAVIOUR EVENTS PER DRIVER (sample) ===")
        result = await conn.execute(text("""
            SELECT d.driver_id, d2.first_name, d2.last_name, COUNT(*) as event_count
            FROM behaviour_events d
            JOIN drivers d2 ON d.driver_id = d2.driver_id
            GROUP BY d.driver_id, d2.first_name, d2.last_name
            LIMIT 5
        """))
        for row in result:
            print(f"  {row}")

        print("\n=== COMPLETED TRIPS PER DRIVER (sample) ===")
        result = await conn.execute(text("""
            SELECT d.driver_id, d2.first_name, d2.last_name, COUNT(*) as trip_count
            FROM trips d
            JOIN drivers d2 ON d.driver_id = d2.driver_id
            WHERE d.status = 'completed'
            GROUP BY d.driver_id, d2.first_name, d2.last_name
            LIMIT 5
        """))
        for row in result:
            print(f"  {row}")

        print("\n=== FUEL EFFICIENCY FROM TRIPS ===")
        result = await conn.execute(text("""
            SELECT COUNT(*), AVG(fuel_used_liters), AVG(distance_km),
                   CASE WHEN SUM(fuel_used_liters) > 0 
                        THEN SUM(distance_km) / SUM(fuel_used_liters) 
                        ELSE 0 END as fleet_fuel_eff
            FROM trips 
            WHERE status = 'completed' AND fuel_used_liters > 0
        """))
        r = result.first()
        print(f"  count={r[0]}, avg_fuel={r[1]}, avg_distance={r[2]}, fleet_fuel_eff={r[3]}")

        print("\n=== EVENTS PER TRIP (completed only) ===")
        result = await conn.execute(text("""
            SELECT COUNT(DISTINCT t.trip_id) as trips_with_events, 
                   (SELECT COUNT(*) FROM trips WHERE status='completed') as total_completed,
                   COUNT(*) as total_events
            FROM behaviour_events e
            JOIN trips t ON e.trip_id = t.trip_id
            WHERE t.status = 'completed'
        """))
        r = result.first()
        print(f"  trips_with_events={r[0]}, total_completed={r[1]}, total_events={r[2]}")

    await engine.dispose()
    print("\nDone.")

asyncio.run(main())
