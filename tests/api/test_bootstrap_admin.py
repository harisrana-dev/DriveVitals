import pytest
from sqlalchemy import select

from backend.api.v1.services.admin_bootstrap import (
    BOOTSTRAP_EMAIL_ENV,
    BOOTSTRAP_NAME_ENV,
    BOOTSTRAP_PASSWORD_ENV,
    AdminBootstrapConfigError,
    bootstrap_admin,
    read_bootstrap_config,
)
from backend.db.models.user import User
from tests.api.conftest import _reset_database, test_session_factory

_BOOTSTRAP_VARS = (
    BOOTSTRAP_EMAIL_ENV,
    BOOTSTRAP_PASSWORD_ENV,
    BOOTSTRAP_NAME_ENV,
)


def _clear_bootstrap_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _BOOTSTRAP_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def bootstrap_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_bootstrap_env(monkeypatch)
    monkeypatch.setenv(BOOTSTRAP_EMAIL_ENV, "admin@example.com")
    monkeypatch.setenv(BOOTSTRAP_PASSWORD_ENV, "Strong-Pass-123")
    monkeypatch.setenv(BOOTSTRAP_NAME_ENV, "Bootstrap Admin")


class TestReadBootstrapConfig:

    def test_returns_none_when_fully_unconfigured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_bootstrap_env(monkeypatch)
        assert read_bootstrap_config() is None

    def test_raises_on_partial_configuration(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_bootstrap_env(monkeypatch)
        monkeypatch.setenv(BOOTSTRAP_EMAIL_ENV, "admin@example.com")

        with pytest.raises(AdminBootstrapConfigError):
            read_bootstrap_config()

    def test_lowercases_email(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_bootstrap_env(monkeypatch)
        monkeypatch.setenv(BOOTSTRAP_EMAIL_ENV, "Admin@Example.COM")
        monkeypatch.setenv(BOOTSTRAP_PASSWORD_ENV, "Strong-Pass-123")
        monkeypatch.setenv(BOOTSTRAP_NAME_ENV, "Bootstrap Admin")

        config = read_bootstrap_config()
        assert config is not None
        assert config.email == "admin@example.com"


class TestBootstrapAdmin:

    async def test_creates_admin_on_empty_database(
        self, bootstrap_env, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        await _reset_database()
        async with test_session_factory() as session:
            result = await bootstrap_admin(session)
            assert result.created is True
            assert result.reason == "created"
            assert result.email == "admin@example.com"

            users = (
                (await session.execute(select(User))).scalars().all()
            )
            assert len(users) == 1
            user = users[0]
            assert user.email == "admin@example.com"
            assert user.role == "admin"
            assert user.is_active is True
            assert user.full_name == "Bootstrap Admin"
            assert user.password_hash.startswith("scrypt")

    async def test_lowercased_email_is_created(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_bootstrap_env(monkeypatch)
        monkeypatch.setenv(BOOTSTRAP_EMAIL_ENV, "Root@Example.com")
        monkeypatch.setenv(BOOTSTRAP_PASSWORD_ENV, "Strong-Pass-123")
        monkeypatch.setenv(BOOTSTRAP_NAME_ENV, "Root Admin")

        await _reset_database()
        async with test_session_factory() as session:
            result = await bootstrap_admin(session)
            assert result.created is True
            assert result.email == "root@example.com"

    async def test_is_idempotent_after_creation(
        self, bootstrap_env
    ) -> None:
        await _reset_database()
        async with test_session_factory() as session:
            first = await bootstrap_admin(session)
            assert first.created is True

            second = await bootstrap_admin(session)
            assert second.created is False
            assert second.reason == "users_exist"

            users = (
                (await session.execute(select(User))).scalars().all()
            )
            assert len(users) == 1

    async def test_noop_when_users_exist(
        self, bootstrap_env
    ) -> None:
        await _reset_database()
        async with test_session_factory() as session:
            from backend.api.security import ScryptPasswordHasher

            from uuid import uuid4

            session.add(
                User(
                    user_id=str(uuid4()),
                    email="existing@example.com",
                    password_hash=ScryptPasswordHasher().hash("whatever"),
                    full_name="Existing User",
                    role="viewer",
                    is_active=True,
                )
            )
            await session.commit()

            result = await bootstrap_admin(session)
            assert result.created is False
            assert result.reason == "users_exist"

            users = (
                (await session.execute(select(User))).scalars().all()
            )
            assert len(users) == 1
            assert users[0].role == "viewer"

    async def test_not_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_bootstrap_env(monkeypatch)
        await _reset_database()
        async with test_session_factory() as session:
            result = await bootstrap_admin(session)
            assert result.created is False
            assert result.reason == "not_configured"

    async def test_partial_config_is_fatal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_bootstrap_env(monkeypatch)
        monkeypatch.setenv(BOOTSTRAP_EMAIL_ENV, "admin@example.com")

        await _reset_database()
        async with test_session_factory() as session:
            with pytest.raises(AdminBootstrapConfigError):
                await bootstrap_admin(session)