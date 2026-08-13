"""
Integration test isolation.

The API suite's websocket tests run the real FastAPI app through
Starlette's ``TestClient``. The app lifespan starts the DriveVitals
runtime on TestClient's own event loop, which pools connections on the
shared ``backend.db.session.engine``. Once that loop closes, any pooled
connection is bound to a dead loop and the next integration test's
``init_db()`` (``pool_pre_ping``) crashes with "Event loop is closed".

Disposing the engine before every integration test purges those stale
cross-loop connections so integration tests are independent of the API
suite's execution order.
"""

import pytest

from backend.db.session import close_db


@pytest.fixture(autouse=True)
async def _dispose_shared_engine() -> None:
    await close_db()
    yield
