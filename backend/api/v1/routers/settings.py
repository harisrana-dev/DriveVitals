from fastapi import APIRouter, Depends

from backend.api.v1.dependencies import (
    require_admin,
)
from backend.api.v1.schemas.common import Response
from backend.api.v1.schemas.settings import SettingsPayload
from backend.db.models.user import User

router = APIRouter(prefix="/settings")


@router.get(
    "",
    response_model=Response[SettingsPayload],
    summary="Read system settings",
    description=(
        "Return the current, safely readable configuration. Administrators "
        "only: operators and viewers receive 403 with "
        "INSUFFICIENT_PERMISSIONS. M2 exposes an explicit empty "
        "configuration structure; settings that change system behaviour "
        "arrive with the Digital Twin milestone."
    ),
    tags=["Settings"],
)
async def get_settings(
    current_user: User = Depends(require_admin),
) -> Response[SettingsPayload]:
    return Response[SettingsPayload](
        data=SettingsPayload(settings={})
    )