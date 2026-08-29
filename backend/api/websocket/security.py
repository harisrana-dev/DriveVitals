from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.security import authenticate_session
from backend.db.models.user import User


async def authenticate_ws(
    websocket: WebSocket,
    session: AsyncSession,
) -> User | None:
    """Resolve the authenticated user from a WebSocket ``?token=`` query.

    This is a read-only helper: it never raises or closes the socket itself
    so the caller decides how to react. It returns ``None`` when no token is
    present, when the token is invalid/expired/revoked, or when the owning
    user is missing or inactive.
    """
    token = websocket.query_params.get("token")
    return await authenticate_session(session, token)