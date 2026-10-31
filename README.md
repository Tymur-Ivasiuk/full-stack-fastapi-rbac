# Role-Based Access Control on the Full Stack FastAPI Template

This repo is [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) (upstream `f4bcfab`) with role-based access control added. There are three roles, **admin**, **manager** and **member**, and the backend and the frontend enforce them the same way.

- [Quick start](#quick-start)
- [Running tests](#running-tests)
- [Database migrations](#database-migrations)
- [Permission matrix](#permission-matrix)
- [Authorization approach](#authorization-approach)
- [Adding a role or a permission](#adding-a-role-or-a-permission)
- Architecture decisions: [ADR-0001](docs/adr/0001-permission-based-rbac-in-code.md), [ADR-0002](docs/adr/0002-frontend-reads-permissions-from-api.md)
- Scope cuts and trade-offs: [NOTES.md](NOTES.md)

## Quick start

**Requirements:** Docker with Compose v2. To run backend tests you also need [uv](https://docs.astral.sh/uv/). For frontend hot reload you also need [bun](https://bun.sh); this is optional.

```bash
# 1. Build and start the stack. The React app is built into the backend image.
docker compose up -d --build --wait backend

# 2. Apply migrations and create the admin from .env (FIRST_SUPERUSER).
docker compose exec backend bash scripts/prestart.sh

# 3. Seed one manager and one member for trying out the roles.
docker compose exec backend python app/seed_demo_users.py
```

Open **http://localhost:8000** for the app, or **http://localhost:8000/docs** for the API docs.

| Account | Password | Role |
|---|---|---|
| `admin@example.com` | `changethis` | admin |
| `manager@example.com` | `changethis` | manager |
| `member@example.com` | `changethis` | member |

The admin credentials come from `.env` (`FIRST_SUPERUSER`, `FIRST_SUPERUSER_PASSWORD`). The seed script is idempotent and refuses to run unless `FASTAPI_ENV=development`, which `compose.override.yml` sets.

> **Port 5432 already in use?** If you run a local Postgres, publish the DB on another port, for example `POSTGRES_HOST_PORT=5433 docker compose up -d --build --wait backend`. Then use that port in `DATABASE_URL` when running tests from the host.

**Frontend with hot reload (optional):** run `bun install && bun run dev` from the repo root, then open http://localhost:5173. The dev server talks to the API on `:8000`.

## Running tests

Backend tests run on the host against the Compose database:

```bash
cd backend
uv sync
uv run bash scripts/test.sh
# with a custom DB port:
# DATABASE_URL=postgresql://postgres:changethis@localhost:5433/app uv run bash scripts/test.sh
```

- Authorization tests are in [`backend/tests/api/routes/test_rbac.py`](backend/tests/api/routes/test_rbac.py). They cover the allowed and denied case for each role, privilege-escalation attempts, the `/users/me` permissions contract, 401 vs 403, and logging of denied attempts.
- The template's test fixtures delete **all** users when the session ends. Run steps 2–3 of the quick start again afterwards to restore the demo accounts.
- To run the end-to-end tests (Playwright, in Docker; this includes the access-denied UI): `CI=1 docker compose run --rm --build playwright bunx playwright test --reporter=line`.

## Database migrations

Migration [`3b7c1e9a4d20`](backend/app/alembic/versions/3b7c1e9a4d20_replace_is_superuser_with_role.py) replaces the `user.is_superuser` boolean with a `user.role` column (`VARCHAR(32)`):

- existing superusers become `admin`, and everyone else becomes `member`;
- the downgrade restores `is_superuser`. It is lossy: managers become regular users.

`scripts/prestart.sh` applies migrations (`alembic upgrade head`). To apply them by hand: `docker compose exec backend alembic upgrade head`.

## Permission matrix

| Action | Endpoint(s) | Permission | admin | manager | member |
|---|---|---|:-:|:-:|:-:|
| List users, view another user | `GET /users/`, `GET /users/{id}` | `users:read` | ✓ | ✓ | ✗ |
| Create a user | `POST /users/` | `users:create` | ✓ | ✗ | ✗ |
| Update or delete any user, assign roles | `PATCH`, `DELETE /users/{id}` | `users:manage` | ✓ | ✗ | ✗ |
| View metrics | `GET /metrics/` | `metrics:read` | ✓ | ✓ | ✗ |
| Global settings (send test email, preview recovery email) | `POST /utils/test-email/`, `POST /password-recovery-html-content/{email}` | `settings:manage` | ✓ | ✗ | ✗ |
| Access other users' items | `/items/*` | `items:manage_all` | ✓ | ✗ | ✗ |
| View and update own profile, change own password | `/users/me`, `/users/me/password` | *(any signed-in user)* | ✓ | ✓ | ✓ |
| Delete own account | `DELETE /users/me` | *(any signed-in user)* | ✗¹ | ✓ | ✓ |
| Create and manage own items | `/items/*` | *(ownership)* | ✓ | ✓ | ✓ |
| Sign up | `POST /users/signup` | *(public)* | always creates a **member** |||

¹ Lockout guard: admins can't delete themselves or change their own role. Another admin has to do it.

**In the UI:**

| Element | Shown when the user has |
|---|---|
| Sidebar **Users** link and the `/admin` page | `users:read` |
| Sidebar **Metrics** link and the `/metrics` page | `metrics:read` |
| **Add User** button | `users:create` |
| Edit/delete menu on user rows | `users:manage` |

Opening a page directly without the permission shows an **Access denied** screen instead of a redirect or a blank page.

## Authorization approach

**Where checks live.** Authorization is done with FastAPI dependencies, not middleware. Each protected endpoint declares `dependencies=[Depends(require_permission(Permission.X))]` ([`app/api/deps.py`](backend/app/api/deps.py)), or the router declares it once, as `/metrics` does. The rule therefore sits right next to the endpoint, so you can read it from the route definition and test it over HTTP. When the check fails the endpoint returns **403** and logs a `WARNING` with the user id, role, permission, method and path. Rules based on ownership ("your own profile", "your own items") can't be expressed as a static permission. They stay inside the route, e.g. `can_access_item()` in `items.py`, which falls back to the `items:manage_all` permission.

**How roles are stored and checked.** A user has exactly one role, stored in `user.role`. It is a plain `VARCHAR`, validated by the `Role` `StrEnum`. [`app/core/permissions.py`](backend/app/core/permissions.py) is the single source of truth: it defines `Role`, `Permission`, and the `ROLE_PERMISSIONS` map from each role to its permission set. The rest of the code checks **permissions, never roles**. The JWT carries only the user id, and the role is loaded from the DB on every request, so a role change takes effect on the user's next request without logging in again. To prevent privilege escalation, `role` is accepted only by the admin-only `PATCH /users/{id}` and `POST /users/`. The self-service schemas (`UserUpdateMe`, `UserRegister`) have no `role` field.

**How the frontend learns capabilities.** `UserPublic` exposes a computed `permissions` list, so `GET /users/me` tells the UI exactly what the current user may do. The role → permission map exists only on the backend. In the UI, `usePermissions().can("users:read")` drives the sidebar filter, the `RequirePermission` page guard and the conditional buttons. These checks only shape the UX; the backend enforces every rule independently. The API client tells **401** (invalid session → log out) apart from **403** (signed in but not allowed → stay signed in and see a message). Before this change the template logged the user out on both.

```mermaid
flowchart LR
    UI["React UI<br/>usePermissions().can(p)<br/>hides links · RequirePermission page guard"]
    subgraph Backend["FastAPI"]
        AuthN["get_current_user<br/>JWT → User (401 if invalid)"]
        AuthZ["require_permission(p)<br/>403 + log if missing"]
        Own["route-level ownership checks<br/>(own profile / own items)"]
        Map[("app/core/permissions.py<br/>ROLE_PERMISSIONS")]
    end
    DB[("PostgreSQL<br/>user.role")]

    UI -- "Bearer token" --> AuthN --> AuthZ --> Own
    AuthN -- "load user + role" --> DB
    AuthZ -. "has_permission(role, p)" .-> Map
    AuthN -- "GET /users/me → role + permissions" --> UI
```

## Adding a role or a permission

**New role:** add it to `Role` and give it a permission set in `ROLE_PERMISSIONS` in [`permissions.py`](backend/app/core/permissions.py). Then regenerate the client (`bash scripts/generate-client.sh`). TypeScript will fail the build until you add a label to `ROLE_LABELS` in [`RoleSelect.tsx`](frontend/src/components/Admin/RoleSelect.tsx). No DB migration is needed, because the column is a plain `VARCHAR`.

**New permission:** add it to `Permission`, assign it to roles in `ROLE_PERMISSIONS`, and protect the endpoint with `require_permission(...)`. In the UI, gate the element with `can("new:permission")`.

## Map of the RBAC code

| Concern | File |
|---|---|
| Roles, permissions, role → permission map | `backend/app/core/permissions.py` |
| `require_permission` dependency, logging of denied access | `backend/app/api/deps.py` |
| `role` column, computed `permissions` on `UserPublic` | `backend/app/models.py` |
| Metrics endpoint | `backend/app/api/routes/metrics.py` |
| Demo seed | `backend/app/seed_demo_users.py` |
| Permission hook | `frontend/src/hooks/usePermissions.ts` |
| Page guard and the Access denied page | `frontend/src/components/Common/RequirePermission.tsx`, `Forbidden.tsx` |
| 401 vs 403 handling | `frontend/src/main.tsx` |

## Base template docs

The template's original documentation still applies: [development.md](development.md), [backend/README.md](backend/README.md), [frontend/README.md](frontend/README.md), [deployment.md](deployment.md).
