from sqlalchemy import select

from backend.db.models.user import User
from backend.db.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    async def find_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        role: str = "operator",
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
        )
        self._session.add(user)
        await self._session.flush()
        return user