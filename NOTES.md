# Notes: scope, trade-offs, next steps

## What was delivered

- Three roles: `admin`, `manager`, `member`. They map to six permissions in `backend/app/core/permissions.py`, which is the single source of truth.
- Backend enforcement through the `require_permission` FastAPI dependency. It returns 403 and logs every denied attempt. Ownership checks for own profile and own items stay inside the routes.
- Migration from `is_superuser` to `role`, with the existing data carried over.
- A `GET /metrics/` endpoint and page: users by role, active users, items.
- Frontend: a permission-aware sidebar, an *Access denied* page on direct navigation, role-gated buttons, and a role select in place of the superuser checkbox.
- Tests: 10 new backend authorization tests, 21 cases once parametrized (`test_rbac.py`), the existing backend and Playwright tests updated for roles, and a demo seed script.

## Decisions and changes beyond the brief

- **401 vs 403.** The template returned 403 for an invalid token, and the UI logged the user out on any 401 *or* 403. With RBAC that would sign a manager out on their first forbidden click. The backend now returns 401 for bad tokens. The UI logs out on 401 only and shows a message on 403. See [ADR-0002](docs/adr/0002-frontend-reads-permissions-from-api.md).
- **Two lockout guards.** An admin can't delete themselves (this was already in the template) and can't change their own role.
- **`POSTGRES_HOST_PORT`** in `compose.override.yml` (default `5432`), so the stack can start next to a local Postgres.

## Deliberate scope cuts

- **No runtime-editable roles or groups**, and one role per user. An Odoo-style ACL in the DB was considered and rejected for this scope ([ADR-0001](docs/adr/0001-permission-based-rbac-in-code.md)). `has_permission()` is the seam where it could be added later.
- **Denied-access logging uses the standard logger** (`WARNING`, `app.api.deps`). There is no persistent audit table.
- **No new role-specific Playwright tests** beyond updating `admin.spec.ts`: the member sees *Access denied* on `/admin` and `/metrics`, and the links are hidden. Backend tests cover the manager's read-only access to users.

## Known gaps

- An admin can still **deactivate their own account** through `PATCH /users/{own id}` (`is_active=false`). There is also no "at least one active admin" check across users. The proper fix is a single "last active admin" check in the user-update and user-delete paths.
- Quirks inherited from the template, left as they are to keep the diff focused: `get_current_user` returns 404 for a deleted user and 400 for an inactive one (401/403 would be more accurate); the backend tests delete *all* users at the end of the session; `tests/` is not copied into the Docker image.

## With more time

1. The last-active-admin invariant described above.
2. A persistent audit log of denied and privileged actions, and a count of denied attempts on the metrics page.
3. Route-level guards (TanStack Router `beforeLoad` with the router context holding the query client), so the page guard doesn't render empty while `/users/me` loads.
4. Playwright tests for each role, e.g. a manager sees the users table without the *Add User* button or row actions.
