# Code Ownership — DriveVitals

This document defines which parts of the codebase each area of the team is primarily responsible for. Ownership doesn't mean exclusivity — it means that person/area should be looped in before significant changes are made there.

---

## Ownership Map

| Area | Paths | Primary Responsibility |
|------|-------|------------------------|
| **Database** | `database/`, `models/`, `migrations/` | Schema design, model relationships, Alembic migrations |
| **Backend** | `backend/api/`, `backend/services/` | API endpoints, request/response contracts, business logic |
| **Analytics** | `backend/analytics/`, `ml/` | Driver behavior, fuel efficiency, vehicle health, predictive maintenance logic |
| **Frontend** | `frontend/` | Dashboard UI, components, data visualization |

```
docs/
database/          ─┐
models/              ├── Database Owner
migrations/         ─┘

backend/api/        ─┐
backend/services/    ├── Backend Owner
                     ─┘

backend/analytics/  ─┐
ml/                   ├── Analytics Owner
                     ─┘

frontend/           ─── Frontend Owner
```

---

## Cross-Boundary Changes

If a change affects an area outside your ownership zone — for example, a frontend change that requires a new API field, or an analytics change that requires a new database column — **do not make that change unilaterally**.

Instead:

1. Open a discussion (in the team channel or as a PR comment) describing what you need and why.
2. Loop in the owner of the affected area.
3. Agree on the interface/contract (e.g. field name, endpoint shape, migration) together.
4. Proceed with implementation once aligned.

This keeps ownership areas internally consistent and prevents silent breaking changes for teammates working in that area.

---

## Why Ownership Matters

- Ensures someone always has full context on each part of the system.
- Reduces accidental breaking changes across layers (e.g. renaming a DB field without updating the backend that reads it).
- Makes code review faster — the owner is the natural first reviewer for changes in their area.
- Doesn't block collaboration — anyone can contribute anywhere, but the owner should be aware of significant changes.