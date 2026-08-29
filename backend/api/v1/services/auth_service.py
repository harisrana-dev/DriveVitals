import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.security import (
    PasswordHasher,
    ScryptPasswordHasher,
    authenticate_session,
    generate_token,
    hash_token,
    session_ttl,
)
from backend.db.models.user import User
from backend.db.repositories.auth_session_repository import AuthSessionRepository
from backend.db.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

MAX_USER_AGENT_LENGTH = 255


class EmailAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class UserInactiveError(Exception):
    pass


class AuthService:
    def __init__(
        self,
        repository: UserRepository,
        session_repository: AuthSessionRepository,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self._repository = repository
        self._session_repository = session_repository
        self._password_hasher = password_hasher or ScryptPasswordHasher()

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    async def signup(
        self,
        email: str,
        password: str,
        full_name: str,
    ) -> User:
        normalized = self._normalize_email(email)
        existing = await self._repository.find_by_email(normalized)
        if existing is not None:
            raise EmailAlreadyExistsError()

        password_hash = self._password_hasher.hash(password)
        user = await self._repository.create(
            email=normalized,
            password_hash=password_hash,
            full_name=full_name,
            role="operator",
        )
        await self._repository._session.commit()
        return user

    async def login(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User, str]:
        normalized = self._normalize_email(email)
        user = await self._repository.find_by_email(normalized)
        if user is None:
            raise InvalidCredentialsError()

        session_repo = self._session_repository
        try:
            valid = self._password_hasher.verify(password, user.password_hash)
        except Exception:
            logger.warning(
                "Unreadable password hash for user %s", user.user_id
            )
            raise InvalidCredentialsError()
        if not valid:
            raise InvalidCredentialsError()
        if not user.is_active:
            raise UserInactiveError()

        now = datetime.now(timezone.utc)
        await session_repo.prune_expired(user.user_id, now)

        token = generate_token()
        await session_repo.create(
            user_id=user.user_id,
            token_hash=hash_token(token),
            expires_at=now + session_ttl(),
            ip_address=ip_address,
            user_agent=(user_agent or "")[:MAX_USER_AGENT_LENGTH] or None,
        )
        await self._repository._session.commit()
        return user, token

    async def logout(self, presented_token: str) -> None:
        session: AsyncSession = self._repository._session
        auth_session = await AuthSessionRepository(session).find_by_token_hash(
            hash_token(presented_token)
        )
        if auth_session is None:
            return
        if auth_session.revoked_at is not None:
            return
        await AuthSessionRepository(session).revoke(
            auth_session.session_id,
            datetime.now(timezone.utc),
        )
        await session.commit()

    async def current_user(self, presented_token: str) -> User | None:
        session: AsyncSession = self._repository._session
        return await authenticate_session(session, presented_token)