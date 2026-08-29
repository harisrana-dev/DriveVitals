from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from httpx import AsyncClient

from backend.api.security import (
    ScryptPasswordHasher,
    generate_token,
    hash_token,
)
from backend.api.websocket.security import authenticate_ws
from backend.db.models import AuthSession, User

_hasher = ScryptPasswordHasher()


def _make_user(
    email="alice@example.com",
    password="password123",
    full_name="Alice Smith",
    role="operator",
    is_active=True,
):
    return User(
        email=email,
        password_hash=_hasher.hash(password),
        full_name=full_name,
        role=role,
        is_active=is_active,
    )


def _create_session_row(
    user,
    token="opaque-token",
    *,
    expires_at=None,
    revoked_at=None,
    last_used_at=None,
):
    return AuthSession(
        session_id="s-1",
        user_id=user.user_id,
        token_hash=hash_token(token),
        expires_at=expires_at or datetime.now(timezone.utc) + timedelta(days=1),
        last_used_at=last_used_at or datetime.now(timezone.utc),
        revoked_at=revoked_at,
    )


async def _signup(client: AsyncClient, **overrides) -> dict:
    payload = {
        "email": "alice@example.com",
        "password": "password123",
        "full_name": "Alice Smith",
    }
    payload.update(overrides)
    response = await client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


async def _login(client: AsyncClient, **overrides) -> dict:
    payload = {
        "email": "alice@example.com",
        "password": "password123",
    }
    payload.update(overrides)
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


class TestSignup:

    async def test_signup_creates_operator_without_token(
        self, client: AsyncClient, session
    ) -> None:
        payload = await _signup(client)

        data = payload["data"]
        assert data["token"] is None
        assert data["user"]["email"] == "alice@example.com"
        assert data["user"]["full_name"] == "Alice Smith"
        assert data["user"]["role"] == "operator"
        assert data["user"]["user_id"]

        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_signup_normalizes_email(self, client: AsyncClient) -> None:
        payload = await _signup(client, email="  Alice@Example.COM ")

        assert payload["data"]["user"]["email"] == "alice@example.com"

    async def test_signup_duplicate_email_conflict(
        self, client: AsyncClient
    ) -> None:
        await _signup(client)
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "alice@example.com",
                "password": "password123",
                "full_name": "Other Name",
            },
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "EMAIL_EXISTS"

    async def test_signup_short_password_rejected(
        self, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "new@example.com",
                "password": "short",
                "full_name": "New User",
            },
        )

        assert response.status_code == 422

    async def test_signup_invalid_email_rejected(
        self, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "not-an-email",
                "password": "password123",
                "full_name": "New User",
            },
        )

        assert response.status_code == 422

    async def test_signup_empty_full_name_rejected(
        self, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "new@example.com",
                "password": "password123",
                "full_name": "",
            },
        )

        assert response.status_code == 422


class TestLogin:

    async def test_login_returns_token_and_user(
        self, client: AsyncClient
    ) -> None:
        await _signup(client)
        payload = await _login(client)

        data = payload["data"]
        assert data["token"]
        assert data["user"]["email"] == "alice@example.com"
        assert data["user"]["role"] == "operator"

    async def test_login_rejects_unknown_email(
        self, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "password123"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "INVALID_CREDENTIALS"

    async def test_login_rejects_wrong_password(
        self, client: AsyncClient
    ) -> None:
        await _signup(client)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "wrong-password"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "INVALID_CREDENTIALS"

    async def test_login_error_is_identical_for_unknown_email_and_wrong_password(
        self, client: AsyncClient
    ) -> None:
        await _signup(client)
        unknown = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "password123"},
        )
        wrong = await client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "wrong-password"},
        )

        assert unknown.status_code == wrong.status_code == 401
        assert unknown.json() == wrong.json()

    async def test_login_rejects_inactive_user(
        self, client: AsyncClient, session
    ) -> None:
        user = _make_user(is_active=False)
        session.add(user)
        await session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "password123"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "INVALID_CREDENTIALS"

    async def test_login_records_user_agent(
        self, client: AsyncClient, session
    ) -> None:
        await _signup(client)
        await client.post(
            "/api/v1/auth/login",
            json={"email": "alice@example.com", "password": "password123"},
            headers={"User-Agent": "test-drivevitals/1.0"},
        )

        from sqlalchemy import select

        rows = list(await session.execute(select(AuthSession)))
        assert len(rows) == 1
        assert rows[0][0].user_agent == "test-drivevitals/1.0"

    async def test_login_prunes_expired_sessions(
        self, client: AsyncClient, session
    ) -> None:
        user = _make_user()
        session.add(user)
        await session.flush()
        session.add(
            _create_session_row(
                user,
                token="expired-token",
                expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            )
        )
        await session.commit()

        await _login(client)
        from sqlalchemy import select

        rows = list(await session.execute(select(AuthSession)))
        assert len(rows) == 1
        assert rows[0][0].token_hash != hash_token("expired-token")


class TestMe:

    async def test_me_requires_token(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert response.json()["detail"] == "INVALID_OR_EXPIRED_TOKEN"

    async def test_me_rejects_garbage_token(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not-a-real-token"},
        )

        assert response.status_code == 401

    async def test_me_returns_public_user_without_secrets(
        self, client: AsyncClient
    ) -> None:
        await _signup(client)
        login = await _login(client)

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login['data']['token']}"},
        )

        assert response.status_code == 200
        user = response.json()["data"]
        assert user["email"] == "alice@example.com"
        assert user["full_name"] == "Alice Smith"
        assert user["role"] == "operator"
        assert "password_hash" not in user
        assert "token_hash" not in user
        assert "is_active" not in user

    async def test_me_rejects_revoked_token(
        self, client: AsyncClient
    ) -> None:
        await _signup(client)
        login = await _login(client)
        token = login["data"]["token"]

        await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_me_rejects_expired_token(
        self, client: AsyncClient, session
    ) -> None:
        user = _make_user()
        session.add(user)
        await session.flush()
        session.add(
            _create_session_row(
                user,
                token="expired-token",
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            )
        )
        await session.commit()

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer expired-token"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "INVALID_OR_EXPIRED_TOKEN"


class TestLogout:

    async def test_logout_revokes_token(self, client: AsyncClient) -> None:
        await _signup(client)
        login = await _login(client)
        token = login["data"]["token"]

        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me.status_code == 401

    async def test_logout_is_idempotent(self, client: AsyncClient) -> None:
        await _signup(client)
        login = await _login(client)
        token = login["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        first = await client.post("/api/v1/auth/logout", headers=headers)
        second = await client.post("/api/v1/auth/logout", headers=headers)

        assert first.status_code == 200
        assert second.status_code == 200

    async def test_logout_requires_token(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 401

    async def test_login_after_logout_creates_fresh_session(
        self, client: AsyncClient
    ) -> None:
        await _signup(client)
        first = await _login(client)
        await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {first['data']['token']}"},
        )

        second = await _login(client)
        assert second["data"]["token"] != first["data"]["token"]
        me = await client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {second['data']['token']}"
            },
        )
        assert me.status_code == 200


class TestTokenFormat:

    def test_tokens_are_opaque_and_stored_hashed(self) -> None:
        token = generate_token()
        assert token != hash_token(token)
        assert len(hash_token(token)) == 64
        assert hash_token(token) != token

    async def test_raw_token_not_stored_in_database(
        self, client: AsyncClient, session
    ) -> None:
        await _signup(client)
        login = await _login(client)
        raw = login["data"]["token"]

        from sqlalchemy import select

        rows = list(await session.execute(select(AuthSession)))
        assert len(rows) == 1
        stored = rows[0][0].token_hash
        assert stored == hash_token(raw)
        assert stored != raw


class TestAuthSessionValidation:

    async def test_valid_session_returns_user(
        self, client: AsyncClient, session
    ) -> None:
        await _signup(client)
        login = await _login(client)
        token = login["data"]["token"]

        from backend.api.security import authenticate_session

        user = await authenticate_session(session, token)
        assert user is not None
        assert user.email == "alice@example.com"

    async def test_one_use_after_revocation_is_rejected(
        self, client: AsyncClient, session
    ) -> None:
        await _signup(client)
        login = await _login(client)
        token = login["data"]["token"]
        await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        from backend.api.security import authenticate_session

        assert await authenticate_session(session, token) is None

    async def test_authenticate_ws_accepts_valid_token(
        self, client: AsyncClient, session
    ) -> None:
        await _signup(client)
        login = await _login(client)
        token = login["data"]["token"]
        websocket = SimpleNamespace(query_params={"token": token})

        user = await authenticate_ws(websocket, session)
        assert user is not None
        assert user.email == "alice@example.com"
        assert user.role == "operator"

    async def test_authenticate_ws_rejects_missing_token(
        self, client: AsyncClient, session
    ) -> None:
        websocket = SimpleNamespace(query_params={})

        assert await authenticate_ws(websocket, session) is None

    async def test_authenticate_ws_rejects_invalid_token(
        self, client: AsyncClient, session
    ) -> None:
        websocket = SimpleNamespace(query_params={"token": "bogus"})

        assert await authenticate_ws(websocket, session) is None

    async def test_authenticate_ws_rejects_expired_token(
        self, client: AsyncClient, session
    ) -> None:
        user = _make_user()
        session.add(user)
        await session.flush()
        session.add(
            _create_session_row(
                user,
                token="expired-websocket-token",
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            )
        )
        await session.commit()
        websocket = SimpleNamespace(
            query_params={"token": "expired-websocket-token"}
        )

        assert await authenticate_ws(websocket, session) is None


class TestBackwardCompatibility:

    async def test_existing_endpoints_stay_anonymous(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/api/v1/vehicles")

        assert response.status_code == 200
        assert response.json()["count"] == 5

    async def test_system_endpoints_stay_anonymous(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/api/v1/system/health")

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "healthy"


class TestRoleNotEnforced:

    async def test_viewer_sessions_are_not_restricted(
        self, client: AsyncClient, session
    ) -> None:
        user = _make_user(role="viewer")
        session.add(user)
        await session.commit()

        login = await _login(client, email="alice@example.com")
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login['data']['token']}"},
        )

        assert response.status_code == 200
        assert response.json()["data"]["role"] == "viewer"