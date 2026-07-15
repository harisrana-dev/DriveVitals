# Contributing to DriveVitals

Thank you for contributing to DriveVitals. This document defines the standards every contribution is expected to meet.

---

## Coding Standards

- Follow **PEP 8** for all Python code.
- Use type hints for function signatures where practical.
- Keep functions focused — if a function is doing more than one clear thing, split it.
- Avoid deeply nested logic; prefer early returns.
- No commented-out dead code in merged PRs — delete it or explain why it's kept.
- Business logic belongs in `services/` or `analytics/`, not directly in API routers (see `BACKEND_GUIDE.md`).

---

## Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Variables / functions | `snake_case` | `calculate_fuel_efficiency()` |
| Classes | `PascalCase` | `TelemetryConsumer` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_ATTEMPTS` |
| Files/modules | `snake_case` | `trip_service.py` |
| Branches | `feature/<name>` or `fix/<name>` | `feature/dashboard-ui` |

---

## Commit Rules

Use the prefix convention from `TEAM_WORKFLOW.md`:

```
feat: add predictive maintenance scoring
fix: correct off-by-one error in trip aggregation
docs: add troubleshooting section to setup guide
refactor: simplify analytics snapshot builder
test: cover edge cases in fuel efficiency calc
chore: update dependency versions
```

- Keep commits focused on a single logical change.
- Write commit messages in the imperative mood ("add", not "added" or "adds").

---

## Pull Request Rules

Every PR must include:

1. **Description** of what the change does and why
2. **Changes made** — bullet list
3. **Testing performed** — how it was verified
4. **Screenshots** — if there's a UI change
5. **At least one reviewer approval** before merging

PRs should target `develop`, never `main` directly.

Keep PRs reasonably small and scoped to one feature or fix — large, sprawling PRs are harder to review and more likely to introduce bugs.

---

## Code Review Rules

As a reviewer:

- Check that the PR does what its description says.
- Verify tests were added or updated where relevant.
- Look for logic that belongs in the wrong layer (e.g. business logic in a router).
- Leave specific, actionable comments rather than vague ones.
- Approve only once you're confident the change is safe to merge into `develop`.

As an author:

- Respond to all review comments, even just to acknowledge them.
- Don't merge your own PR without approval, even if it feels urgent — ping the reviewer instead.

---

## Testing Requirements

- New features should include at least basic unit tests covering the core logic.
- Bug fixes should include a test that would have caught the bug.
- Run the full test suite locally before opening a PR.
- Do not merge a PR with failing tests.

---

## Documentation Requirements

- If you add a new model, endpoint, or module, update the relevant doc in `docs/team/` (e.g. `DATABASE_GUIDE.md`, `BACKEND_GUIDE.md`).
- If your change affects the setup process, update `DEVELOPMENT_SETUP.md`.
- Keep documentation changes in the same PR as the code change when possible, so they never drift out of sync.