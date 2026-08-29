"""First-administrator bootstrap for an empty deployment.

Environment-based provisioning:

    BOOTSTRAP_ADMIN_EMAIL
    BOOTSTRAP_ADMIN_PASSWORD
    BOOTSTRAP_ADMIN_NAME

Behaves exactly once: when a fresh database has no users AND all three
bootstrap variables are configured, the first user is created as an
``admin``. Existing users are never promoted or altered, and partial
configuration fails loudly instead of guessing.

Secrets (password, password hash, tokens) are never logged.
"""

import os
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.security import ScryptPasswordHasher
from backend.db.repositories import UserRepository

BOOTSTRAP_EMAIL_ENV = "BOOTSTRAP_ADMIN_EMAIL"
BOOTSTRAP_PASSWORD_ENV = "BOOTSTRAP_ADMIN_PASSWORD"
BOOTSTRAP_NAME_ENV = "BOOTSTRAP_ADMIN_NAME"

_BOOTSTRAP_ENV_VARS = (
    BOOTSTRAP_EMAIL_ENV,
    BOOTSTRAP_PASSWORD_ENV,
    BOOTSTRAP_NAME_ENV,
)

_hasher = ScryptPasswordHasher()


class AdminBootstrapConfigError(Exception):
    """Raised when the bootstrap environment is incomplete."""


@dataclass(frozen=True)
class BootstrapConfig:
    email: str
    password: str
    full_name: str


@dataclass(frozen=True)
class AdminBootstrapResult:
    created: bool
    reason: str
    email: str | None = None


def read_bootstrap_config() -> BootstrapConfig | None:
    """Read the bootstrap environment, or ``None`` when it is unconfigured.

    Raises :class:`AdminBootstrapConfigError` when only some variables are
    configured — a partial configuration is a deployment error.
    """
    values = {
        name: os.environ.get(name, "").strip()
        for name in _BOOTSTRAP_ENV_VARS
    }
    configured = {name: value for name, value in values.items() if value}

    if not configured:
        return None

    missing = [name for name in _BOOTSTRAP_ENV_VARS if not values[name]]
    if missing:
        raise AdminBootstrapConfigError(
            "BOOTSTRAP_ADMIN_* environment is partially configured; "
            f"missing: {', '.join(missing)}. Configure all three "
            "variables or remove them."
        )

    return BootstrapConfig(
        email=values[BOOTSTRAP_EMAIL_ENV].lower(),
        password=values[BOOTSTRAP_PASSWORD_ENV],
        full_name=values[BOOTSTRAP_NAME_ENV],
    )


async def bootstrap_admin(session: AsyncSession) -> AdminBootstrapResult:
    """Provision the first administrator when appropriate. Idempotent."""
    config = read_bootstrap_config()
    if config is None:
        return AdminBootstrapResult(
            created=False,
            reason="not_configured",
        )

    repository = UserRepository(session)
    if await repository.count_all() > 0:
        return AdminBootstrapResult(
            created=False,
            reason="users_exist",
        )

    user = await repository.create(
        email=config.email,
        password_hash=_hasher.hash(config.password),
        full_name=config.full_name,
        role="admin",
    )
    await session.commit()

    return AdminBootstrapResult(
        created=True,
        reason="created",
        email=user.email,
    )