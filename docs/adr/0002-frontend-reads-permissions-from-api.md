# ADR-0002: The frontend reads resolved permissions from `/users/me`

- **Status:** Accepted
- **Date:** 2026-10-31

## Context

The UI must hide navigation links and buttons the user can't use, and show a friendly *Access denied* page when someone opens a protected URL directly. To do this the frontend has to know the current user's capabilities. Whatever we choose, the backend stays the authority: frontend checks only shape the UX.

The template also had a related problem. Its API client treated **every** 401 *and* 403 as "session expired": it cleared the token and redirected to `/login`. With RBAC, one forbidden request would log a manager out.

## Options considered

1. **Send only `role`, and duplicate the role → permission map in TypeScript.** Simple API, but two copies of the map drift apart. A new role or a changed grant must be edited in two languages, and nothing catches a mismatch.
2. **Check roles directly in components** (`user.role === "admin"`). This scatters the authorization model across the UI, and every new role means hunting through components.
3. **Put permissions in the JWT claims.** No extra field on the user, but permissions go stale until the token expires (8 days in this template), and the token grows.
4. **Return the resolved `permissions` list in `GET /users/me`.** The backend computes it from `ROLE_PERMISSIONS`. The UI asks only `can(permission)`.

## Decision

We chose **option 4**.

- `UserPublic` has a computed `permissions: list[Permission]` field. It appears in the OpenAPI schema, so the generated TypeScript client types it as the `Permission` union.
- `usePermissions().can(p)` is the only way the UI checks authorization. The sidebar items, the `<RequirePermission>` page guard and the conditional buttons all use it.
- On direct navigation, `<RequirePermission>` renders a `Forbidden` page in place of the page. It does not redirect, so the URL stays and the user learns why.
- Status codes are now distinct. The backend returns **401** for an invalid token (it was 403) and **403** for a missing permission. The client logs the user out on 401 only. On 403 it keeps the session and shows a toast; mutations show the backend's message.

## Consequences

- The role → permission map has exactly one copy. Changing a grant on the backend changes the UI with no frontend edit.
- Permission names are typed end to end. A typo like `can("user:read")` fails `tsc`.
- The role change of a signed-in user shows up in the UI when `/users/me` is refetched, e.g. on page reload. The backend enforces the change immediately anyway.
- The UI still needs labels for roles (the role select in the admin forms). They live in one `Record<Role, string>`, which the compiler forces to stay complete.
