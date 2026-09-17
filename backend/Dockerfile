# DriveVitals backend image.
#
# Shared by BOTH the "migration" service (runs `alembic upgrade head`)
# and the "backend" service (runs uvicorn). Dependency versions are pinned
# in backend/requirements.txt to the known-good set used by CI and local
# development so every team member builds the same image.
#
# Build context is the repository root:  docker build -f backend/Dockerfile .

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python dependencies before copying code so dependency layers are
# cached independently of application changes.
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install -r /app/backend/requirements.txt

COPY backend /app/backend

# The application is imported as `backend.api.main`, so the repository
# root must be on the Python path.
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]