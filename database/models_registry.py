"""
DriveVitals SQLAlchemy Model Registry

Imports all models so Alembic can detect tables.
"""

# Fleet domain
from database.models.fleet import Fleet
from database.models.vehicle import Vehicle
from database.models.driver import Driver
from database.models.trip import Trip

# Telemetry domain
from database.models.telemetry import Telemetry

# Analytics domain
from database.models.analytics_snapshot import AnalyticsSnapshot

# Future models
from database.models.alerts import Alert
from database.models.maintenance import MaintenanceEvent