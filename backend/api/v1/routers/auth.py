from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.api.v1.dependencies import (
    get_auth_service,
    get_current_user,
)
from backend.api.v1.schemas.auth import (
    LoginRequest,
    SignupRequest,
    UserRead,
    UserWithToken,
)
from backend.api.v1.schemas.common import Response
from backend.api.v1.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserInactiveError,
)
from backend.db.models.user import User

router = APIRouter(prefix="/auth")

_bearer = HTTPBearer(auto_error=False)


def _public_user(user: User) -> UserRead:
    return UserRead(
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    )


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post(
    "/signup",
    response_model=Response[UserWithToken],
    summary="Create a user account",
    description=(
        "Register a new operator account. The account becomes immediately "
        "usable but is not automatically signed in; a login is required to "
        "obtain a session token."
    ),
    tags=["Auth"],
)
async def signup(
    payload: SignupRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> Response[UserWithToken]:
    try:
        user = await service.signup(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
        )
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail="EMAIL_EXISTS",
        )
    return Response[UserWithToken](
        data=UserWithToken(
            token=None,
            user=_public_user(user),
        )
    )


@router.post(
    "/login",
    response_model=Response[UserWithToken],
    summary="Log in",
    description=(
        "Exchange valid credentials for an opaque session token. Unknown "
        "emails and wrong passwords return the same error to avoid account "
        "enumeration."
    ),
    tags=["Auth"],
)
async def login(
    payload: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> Response[UserWithToken]:
    try:
        user, token = await service.login(
            email=payload.email,
            password=payload.password,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except (InvalidCredentialsError, UserInactiveError):
        raise HTTPException(
            status_code=401,
            detail="INVALID_CREDENTIALS",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Response[UserWithToken](
        data=UserWithToken(
            token=token,
            user=_public_user(user),
        )
    )


@router.post(
    "/logout",
    response_model=Response[None],
    summary="Log out",
    description=(
        "Revoke the presented session token. Idempotent: revoking an "
        "unknown or already-revoked token still succeeds."
    ),
    tags=["Auth"],
)
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    service: AuthService = Depends(get_auth_service),
) -> Response[None]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="INVALID_OR_EXPIRED_TOKEN",
            headers={"WWW-Authenticate": "Bearer"},
        )
    await service.logout(credentials.credentials)
    return Response[None](data=None)


@router.get(
    "/me",
    response_model=Response[UserRead],
    summary="Authenticated user",
    description=(
        "Return the profile of the authenticated user. Requires a valid "
        "bearer token."
    ),
    tags=["Auth"],
)
async def me(
    current_user: User = Depends(get_current_user),
) -> Response[UserRead]:
    return Response[UserRead](data=_public_user(current_user))