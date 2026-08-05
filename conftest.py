import os

# ---------------------------------------------------------------------------
# Test database isolation.
#
# The API test suite drops and reseeds its database on every session. It must
# therefore NEVER target the development runtime database (drivevitals_dev).
#
# This module is imported by pytest before any other test module, so we force
# the database name onto a dedicated test database here. Override with the
# DRIVEVITALS_TEST_DB environment variable if a different test database is
# preferred; the default keeps tests fully isolated from the runtime.
# ---------------------------------------------------------------------------

os.environ["POSTGRES_DB"] = os.environ.get("DRIVEVITALS_TEST_DB", "drivevitals_test")
