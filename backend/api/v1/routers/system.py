import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.schemas.common import Response
from backend.db.session import get_session

APP_NAME = "DriveVitals"
APP_VERSION = "1.0.0"
API_VERSION = "v1"

router = APIRouter(prefix="/system")

_process_started_at = time.time()


class HealthRead(BaseModel):
    status: str
    database: str


class VersionRead(BaseModel):
    name: str
    version: str
    api_version: str


class StatusRead(BaseModel):
    name: str
    status: str
    version: str
    api_version: str
    uptime_seconds: int


@router.get(
    "/health",
    response_model=Response[HealthRead],
    summary="System health",
    description=(
        "Report the health of the DriveVitals API, including database "
        "connectivity."
    ),
    tags=["System"],
)
async def system_health(
    session: AsyncSession = Depends(get_session),
) -> Response[HealthRead]:
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Database is unreachable",
        )

    return Response[HealthRead](
        data=HealthRead(status="healthy", database="connected")
    )


@router.get(
    "/version",
    response_model=Response[VersionRead],
    summary="System version",
    description="Return the DriveVitals application and API version.",
    tags=["System"],
)
async def system_version() -> Response[VersionRead]:
    return Response[VersionRead](
        data=VersionRead(
            name=APP_NAME,
            version=APP_VERSION,
            api_version=API_VERSION,
        )
    )


@router.get(
    "/status",
    response_model=Response[StatusRead],
    summary="System status",
    description="Return the operational status of the DriveVitals API.",
    tags=["System"],
)
async def system_status() -> Response[StatusRead]:
    return Response[StatusRead](
        data=StatusRead(
            name=APP_NAME,
            status="operational",
            version=APP_VERSION,
            api_version=API_VERSION,
            uptime_seconds=int(time.time() - _process_started_at),
        )
    )
