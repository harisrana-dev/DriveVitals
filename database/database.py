"""
DriveVitals Database Configuration

Creates the SQLAlchemy Engine that connects
FastAPI to the PostgreSQL database.
"""

from sqlalchemy import create_engine

DATABASE_URL = (
    "postgresql://drivevitals:drivevitals123@localhost:5432/drivevitals"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True
)