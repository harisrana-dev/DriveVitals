"""Settings router — admin-only configuration console.

GET  /settings           → full settings payload (account + system + analytics)
GET  /settings/{category} → single category
PATCH /settings/{category} → update a category (admin-only)
"""

import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from backend.api.v1.dependencies import (
    get_settings_service,
    require_admin,
)
from backend.api.v1.schemas.common import Response
from backend.api.v1.services.settings_service import SettingsService
from backend.db.models.user import User

router = APIRouter(prefix="/settings")

# Module-level start time for uptime calculation
_process_started_at = time.time()


@router.get(
    "",
    response_model=Response[dict],
    summary="Read all settings",
    description=(
        "Return the complete admin settings payload: account identity, "
        "system information, and analytics configuration.  Administrators "
        "only."
    ),
    tags=["Settings"],
)
async def get_settings(
    current_user: User = Depends(require_admin),
    service: SettingsService = Depends(get_settings_service),
) -> Response[dict]:
    uptime = int(time.time() - _process_started_at)
    data = await service.get_full_settings(current_user, uptime_seconds=uptime)
    return Response[dict](data=data)


@router.get(
    "/{category}",
    response_model=Response[dict],
    summary="Read a settings category",
    description="Return a single configuration category.  Administrators only.",
    tags=["Settings"],
)
async def get_settings_category(
    category: str,
    current_user: User = Depends(require_admin),
    service: SettingsService = Depends(get_settings_service),
) -> Response[dict]:
    uptime = int(time.time() - _process_started_at)
    result = await service.get_category(category, uptime_seconds=uptime)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown settings category: {category}",
        )
    return Response[dict](data=result)


@router.patch(
    "/{category}",
    response_model=Response[dict],
    summary="Update a settings category",
    description=(
        "Validate and persist an update to a configuration category.  "
        "Administrators only."
    ),
    tags=["Settings"],
)
async def update_settings_category(
    category: str,
    body: dict,
    current_user: User = Depends(require_admin),
    service: SettingsService = Depends(get_settings_service),
) -> Response[dict]:
    try:
        result = await service.update_category(category, body, current_user)
    except PydanticValidationError as exc:
        # Convert pydantic errors to JSON-serializable format
        errors = []
        for err in exc.errors():
            errors.append({
                "field": "->".join(str(loc) for loc in err.get("loc", [])),
                "message": str(err.get("msg", "")),
                "type": err.get("type", ""),
            })
        raise HTTPException(
            status_code=422,
            detail=errors,
        )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown settings category: {category}",
        )
    return Response[dict](data=result)
