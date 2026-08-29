import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.user import User
from backend.db.repositories.auth_session_repository import AuthSessionRepository
from backend.db.repositories.user_repository import UserRepository

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_KEY_LEN = 32

_ENCODING = "utf-8"


def _default_token_ttl_hours() -> int:
    raw = os.getenv("ACCESS_TOKEN_TTL_HOURS", "24")
    try:
        value = int(raw)
    except ValueError:
        return 24
    return value if value > 0 else 24


class PasswordVerificationError(Exception):
    """Raised when a stored password hash cannot be verified."""


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, stored: str) -> bool: ...


class ScryptPasswordHasher:
    """PBKDF-alike scrypt password hasher using only the stdlib.

    The stored representation is::

        scrypt$<n>$<r>$<p>$<salt_hex>$<hash_hex>

    It contains every parameter required to recreate the derived key, so
    verification never depends on the caller remembering parameters.
    """

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        derived = hashlib.scrypt(
            password.encode(_ENCODING),
            salt=salt,
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
            dklen=SCRYPT_KEY_LEN,
        )
        return (
            f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}$"
            f"{salt.hex()}${derived.hex()}"
        )

    def verify(self, password: str, stored: str) -> bool:
        parts = stored.split("$")
        if len(parts) != 6 or parts[0] != "scrypt":
            raise PasswordVerificationError("Unsupported stored password format")
        try:
            n = int(parts[1])
            r = int(parts[2])
            p = int(parts[3])
            salt = bytes.fromhex(parts[4])
            expected = bytes.fromhex(parts[5])
        except ValueError:
            raise PasswordVerificationError("Malformed stored password hash")
        candidate = hashlib.scrypt(
            password.encode(_ENCODING),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=len(expected),
        )
        return hmac.compare_digest(candidate, expected)


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode(_ENCODING)).hexdigest()


async def authenticate_session(
    session: AsyncSession,
    presented_token: str | None,
    now: datetime | None = None,
) -> User | None:
    """Validate a presented bearer token and return its user.

    Returns ``None`` for a missing token, an unknown token, a revoked or
    expired session, or an inactive user. Valid sessions have their
    ``last_used_at`` refreshed.
    """
    if not presented_token:
        return None

    if now is None:
        now = datetime.now(timezone.utc)

    session_repo = AuthSessionRepository(session)
    user_repo = UserRepository(session)

    auth_session = await session_repo.find_by_token_hash(
        hash_token(presented_token)
    )
    if auth_session is None:
        return None
    if auth_session.revoked_at is not None:
        return None
    if auth_session.expires_at <= now:
        return None

    user = await user_repo.find_by_id(auth_session.user_id)
    if user is None or not user.is_active:
        return None

    await session_repo.touch(auth_session.session_id, last_used_at=now)
    return user


def session_ttl() -> timedelta:
    return timedelta(hours=_default_token_ttl_hours())