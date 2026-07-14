"""
DriveVitals Database Session

Provides SQLAlchemy sessions for database
transactions.
"""

from sqlalchemy.orm import sessionmaker

from database.database import engine

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)