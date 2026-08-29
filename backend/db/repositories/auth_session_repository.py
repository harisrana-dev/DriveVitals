from datetime import datetime, timezone

from sqlalchemy import delete, select, update

from backend.db.models.auth_session import AuthSession
from backend.db.repositories.base_repository import BaseRepository


class AuthSessionRepository(BaseRepository):
    async def find_by_token_hash(self, token_hash: str) -> AuthSession | None:
        result = await self._session.execute(
            select(AuthSession).where(AuthSession.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuthSession:
        session = AuthSession(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            last_used_at=datetime.now(timezone.utc),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(session)
        await self._session.flush()
        return session

    async def revoke(self, session_id: str, revoked_at: datetime) -> bool:
        result = await self._session.execute(
            update(AuthSession)
            .where(AuthSession.session_id == session_id)
            .values(revoked_at=revoked_at)
        )
        await self._session.flush()
        return (result.rowcount or 0) > 0

    async def touch(self, session_id: str, last_used_at: datetime) -> None:
        await self._session.execute(
            update(AuthSession)
            .where(AuthSession.session_id == session_id)
            .values(last_used_at=last_used_at)
        )
        await self._session.flush()

    async def prune_expired(self, user_id: str, now: datetime) -> int:
        result = await self._session.execute(
            delete(AuthSession).where(
                AuthSession.user_id == user_id,
                AuthSession.expires_at < now,
            )
        )
        await self._session.flush()
        return result.rowcount or 0