# ADR-0001: Single role column with a code-defined role → permission map

- **Status:** Accepted
- **Date:** 2026-10-31

## Context

The template has one authorization flag, `user.is_superuser`, and checks it ad hoc in about 20 places across the backend and frontend. We need three roles (admin, manager, member) whose rights differ on users, metrics and settings. Adding a role must stay cheap, and a teammate should understand the model in five minutes. The work has a one-hour timebox.

## Options considered

1. **Add `role` and keep `is_superuser`.** Smallest diff, but it leaves two sources of truth that can disagree (e.g. a `member` who is also a superuser).
2. **A single `role` column, with the role → permission map in code.** One enum column. A Python module maps each role to a set of permissions, and endpoints check permissions only.
3. **Groups and ACLs in the database, in the style of Odoo** (`group`, `user_group`, `model_access`, `record_rule`). Supports multiple groups per user and roles editable at runtime, plus row-level rules. It needs seeding, caching, an admin UI and several migrations, so it is far beyond the timebox. It is also hard to understand in five minutes.
4. **Many-to-many `user_role` with permissions in code.** Allows several roles per user, which none of our three hierarchical roles needs.

## Decision

We chose **option 2**.

- `user.role` is a `VARCHAR(32)` validated by `Role(StrEnum)`. It is deliberately not a native Postgres enum, so adding a role never needs an `ALTER TYPE` migration.
- `backend/app/core/permissions.py` holds `Role`, `Permission` and `ROLE_PERMISSIONS`. It is the only place that knows which role can do what.
- Endpoints declare `Depends(require_permission(Permission.X))`. Code outside `permissions.py` never compares roles, with one deliberate exception: the lockout guard that stops an admin from deleting themselves.
- Actions on one's *own* data (profile, items) are granted by ownership, not by a permission.
- The migration moves `is_superuser = true` to `admin` and drops the column, so there is exactly one source of truth.

## Consequences

- **Adding a role** means one enum value plus one map entry in Python, and one label in the frontend. The build enforces the label after the client is regenerated. No migration is needed.
- **Endpoints are self-describing:** the required permission is visible in the route signature, and it is easy to test with a parametrized "role × endpoint → status" test.
- **Changing permissions requires a deploy.** That is acceptable for three fixed roles. If runtime-editable roles are ever needed, option 3 can replace `ROLE_PERMISSIONS` behind the same `has_permission(role, permission)` function without touching endpoints.
- Each user has exactly one role. The roles nest (member ⊂ manager ⊂ admin), so this is enough today.
- The role is read from the DB on each request (the JWT has only the user id), so a demotion takes effect on the user's next request.
