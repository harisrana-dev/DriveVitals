# Development Setup — DriveVitals

This guide walks a new team member through setting up DriveVitals from a completely clean machine to a running local instance.

---

## 1. Requirements

Install the following before starting:

| Tool | Purpose |
|------|---------|
| **Python 3.10+** | Backend runtime |
| **Git** | Version control |
| **Docker Desktop** | Runs PostgreSQL locally |
| **VS Code** | Recommended editor |

Verify installations:

```bash
python --version
git --version
docker --version
```

---

## 2. Clone the Repository

```bash
git clone https://github.com/harisrana-dev/DriveVitals
cd DriveVitals
```

---

## 3. Virtual Environment Setup

A virtual environment isolates DriveVitals' Python dependencies from the rest of your system.

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

You'll know it worked when your terminal prompt shows `(venv)` at the start.

---

## 4. Installing Dependencies

With the virtual environment active:

```bash
pip install -r requirements.txt
```

---

## 5. Docker Setup (PostgreSQL)

DriveVitals uses **PostgreSQL** running inside a Docker container, managed via `docker-compose.yml`. You do not need to install PostgreSQL directly on your machine.

### Start the database

```bash
docker compose up -d
```

This starts the container in detached mode.

### Check running containers

```bash
docker ps
```

You should see a `postgres` container listed as `Up`.

### View database logs

```bash
docker logs drivevitals
```

### Stop the database

```bash
docker compose down
```

> Use `docker compose down` (not `docker compose down -v`) unless you intentionally want to wipe the database volume.

---

## 6. Database Migrations (Alembic)

DriveVitals uses **Alembic** to manage database schema changes.

### Apply all migrations

```bash
alembic upgrade head
```

Run this after first cloning the repo, and any time you pull changes that include new migrations.

### Create a new migration

When you change a SQLAlchemy model:

```bash
alembic revision --autogenerate -m "add maintenance_event table"
```

Then review the generated migration file before applying it with `alembic upgrade head`.

---

## 7. Environment Variables

Create a `.env` file in the project root (never commit this file):

```env
DATABASE_URL=postgresql://drivevitals_user:drivevitals_pass@localhost:5432/drivevitals_db

POSTGRES_USER=drivevitals_user
POSTGRES_PASSWORD=drivevitals_pass
POSTGRES_DB=drivevitals_db
```

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Full connection string used by SQLAlchemy |
| `POSTGRES_USER` | Database user (must match docker-compose config) |
| `POSTGRES_PASSWORD` | Database password |
| `POSTGRES_DB` | Database name |

---

## 8. Running the Backend

With the virtual environment active and the database running:

```bash
uvicorn backend.main:app --reload
```

The API should now be available at `http://localhost:8000`, and interactive docs at `http://localhost:8000/docs`.

---

## 9. Verifying the Setup

Checklist for a successful setup:

- [ ] `docker ps` shows the Postgres container running
- [ ] `alembic upgrade head` completes with no errors
- [ ] `uvicorn backend.main:app --reload` starts without errors
- [ ] `http://localhost:8000/docs` loads in the browser

---

## 10. Troubleshooting

| Problem | Likely Cause | Fix |
|---------|--------------|-----|
| `docker: command not found` | Docker Desktop not installed or not started | Install/start Docker Desktop |
| Backend can't connect to DB | Postgres container not running | Run `docker compose up -d`, check `docker ps` |
| `alembic.util.exc.CommandError` | Migrations out of sync | Confirm `.env` DATABASE_URL is correct, then re-run `alembic upgrade head` |
| `ModuleNotFoundError` | Virtual environment not activated, or dependencies not installed | Activate `venv`, re-run `pip install -r requirements.txt` |
| Port `5432` already in use | Another Postgres instance running locally | Stop the other instance or change the exposed port in `docker-compose.yml` |
| Changes to models not reflected in DB | Forgot to generate/apply migration | Run `alembic revision --autogenerate -m "..."` then `alembic upgrade head` |

If you're still stuck after trying the above, ask in the team channel before spending more than 30 minutes debugging environment issues — it's often a one-line fix someone else has already hit.