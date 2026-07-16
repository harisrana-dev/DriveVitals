# Team Workflow — DriveVitals

## Overview

DriveVitals is developed using a **feature-branch workflow** built around three tiers of branches: `main`, `develop`, and short-lived `feature/` or `fix/` branches. This document explains how the team collaborates, how branches are structured, and the rules everyone follows to keep the codebase stable.

The goal of this workflow is simple: **`main` should always be deployable, `develop` should always be a working integration point, and all new work happens in isolated branches** that get reviewed before merging.

---

## Branch Strategy

```
main
 └── develop
      ├── feature/telemetry-system
      ├── feature/dashboard-ui
      ├── feature/analytics-engine
      ├── fix/database-error
      └── fix/websocket-bug
```

### `main`

- Production / stable branch.
- Always represents a working, deployable state of DriveVitals.
- **No direct commits.**
- Updated **only** through Pull Requests merged from `develop`.

### `develop`

- Integration branch where all completed features come together.
- Features are tested here before being promoted to `main`.
- Should always build and run, even if not production-ready.

### Feature Branches

- Every developer creates their own branch off `develop` for any new piece of work.
- Never worked on directly by more than one person at a time.
- Deleted after the Pull Request is merged.

---

## Branch Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| New feature | `feature/<feature-name>` | `feature/telemetry-system` |
| Bug fix | `fix/<bug-name>` | `fix/database-error` |

More examples:

```
feature/telemetry-system
feature/dashboard-ui
feature/analytics-engine

fix/database-error
fix/websocket-bug
```

Use lowercase, hyphen-separated names. Keep them short but descriptive.

---

## Complete Developer Workflow

1. **Clone the repository**
2. **Configure Git** (name/email, once per machine)
3. **Pull the latest `develop` branch**
4. **Create a feature branch**
5. **Work on the assigned feature**
6. **Test changes locally**
7. **Commit changes** with meaningful messages
8. **Push the feature branch** to the remote
9. **Create a Pull Request** into `develop`
10. **Review and merge**

### Step-by-Step Commands

```bash
# 1. Clone the repository
git clone <repository-url>
cd drivevitals

# 2. Configure Git (first time only)
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# 3. Pull latest develop branch
git checkout develop
git pull origin develop

# 4. Create a feature branch
git checkout -b feature/telemetry-system

# 5. Work on your feature...
#    (edit files, run tests locally)

# 6. Stage and commit changes
git add .
git commit -m "feat: add OBD-II telemetry parser"

# 7. Push feature branch
git push origin feature/telemetry-system

# 8. Open a Pull Request on GitHub targeting develop
```

---

## Pull Request Rules

Every Pull Request **must** contain:

- [ ] **Description** — what the PR does and why
- [ ] **Changes made** — bullet list of key changes
- [ ] **Testing performed** — how you verified it works
- [ ] **Screenshots** — required if there are UI changes
- [ ] **Reviewer approval** — at least one teammate must approve before merge

### Example PR Description Template

```markdown
## Description
Adds real-time telemetry ingestion via WebSocket from the vehicle simulator.

## Changes Made
- New `TelemetryConsumer` service
- WebSocket route in `backend/websocket/`
- Updated `Telemetry` model with two new fields

## Testing Performed
- Ran simulator locally and confirmed data appears in DB
- Added unit test for payload parsing

## Screenshots
(N/A — backend only)
```

---

## Commit Message Convention

DriveVitals follows a simplified Conventional Commits style:

| Prefix | Use for |
|--------|---------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only changes |
| `refactor:` | Code change that neither fixes a bug nor adds a feature |
| `test:` | Adding or updating tests |
| `chore:` | Maintenance tasks, config, dependencies |

### Examples

```
feat: add fuel efficiency calculation to analytics engine
fix: resolve websocket disconnect on idle timeout
docs: update database guide with AnalyticsSnapshot model
refactor: extract trip aggregation logic into service layer
test: add unit tests for driver behavior scoring
chore: bump fastapi and sqlalchemy versions
```

---

## Team Rules

### Never

- Push directly to `main`
- Push directly to `develop`
- Commit `.env` files
- Commit virtual environments (`venv/`, `.venv/`)
- Overwrite other people's work (force-push shared branches, manual conflict overwrites without discussion)

### Always

- Create a branch for any change, no matter how small
- Pull the latest `develop` before starting new work
- Write meaningful, descriptive commit messages
- Test your changes locally before opening a PR
- Ask before touching code outside your ownership area (see `CODE_OWNERSHIP.md`)

---

## Summary Diagram

```
 ┌─────────┐     PR only      ┌──────────┐     PR only      ┌───────────────────┐
 │  main   │ <───────────────  │ develop  │ <───────────────  │ feature/fix branch │
 └─────────┘                   └──────────┘                   └───────────────────┘
   stable                       integration                     active development
```