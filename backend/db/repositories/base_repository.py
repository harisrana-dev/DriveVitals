import logging

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
