"""
Maintenance Type enum.

Single source of truth for every maintenance service type DriveVitals can
recommend or record. Shared by MaintenanceRecommendation (upcoming work)
and MaintenanceRecord (scheduled or completed work) so the two always
speak the same vocabulary.
"""

from enum import Enum


class MaintenanceType(str, Enum):
    """One value per maintenance service the system can plan or track."""

    OIL_CHANGE = "oil_change"
    ENGINE_INSPECTION = "engine_inspection"
    SPARK_PLUG_SERVICE = "spark_plug_service"

    BRAKE_PAD_REPLACEMENT = "brake_pad_replacement"
    BRAKE_FLUID_SERVICE = "brake_fluid_service"
    BRAKE_INSPECTION = "brake_inspection"

    COOLANT_FLUSH = "coolant_flush"
    COOLING_SYSTEM_INSPECTION = "cooling_system_inspection"
    RADIATOR_INSPECTION = "radiator_inspection"

    TRANSMISSION_SERVICE = "transmission_service"
    TRANSMISSION_INSPECTION = "transmission_inspection"

    FUEL_FILTER_REPLACEMENT = "fuel_filter_replacement"
    INJECTOR_CLEANING = "injector_cleaning"
    FUEL_PUMP_INSPECTION = "fuel_pump_inspection"

    TIRE_REPLACEMENT = "tire_replacement"
    OTHER = "other"


__all__ = ["MaintenanceType"]
