import logging
from datetime import datetime

from backend.db.models.telemetry_sample import TelemetrySample
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class TelemetryRepository(BaseRepository):
    async def insert(
        self,
        trip_id: str,
        vehicle_id: str,
        timestamp: datetime,
        speed_kmh: float,
        rpm: float,
        engine_load_percent: float,
        throttle_percent: float,
        brake_percent: float,
        fuel_rate_lph: float,
        fuel_level_percent: float,
        coolant_temperature_c: float,
        odometer_km: float,
    ) -> TelemetrySample:
        sample = TelemetrySample(
            trip_id=trip_id,
            vehicle_id=vehicle_id,
            timestamp=timestamp,
            speed_kmh=speed_kmh,
            rpm=rpm,
            engine_load_percent=engine_load_percent,
            throttle_percent=throttle_percent,
            brake_percent=brake_percent,
            fuel_rate_lph=fuel_rate_lph,
            fuel_level_percent=fuel_level_percent,
            coolant_temperature_c=coolant_temperature_c,
            odometer_km=odometer_km,
        )
        self._session.add(sample)
        await self._session.flush()
        return sample
