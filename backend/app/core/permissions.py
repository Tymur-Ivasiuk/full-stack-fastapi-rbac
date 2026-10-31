"""Role-based access control: the single source of truth.

Code outside this module checks *permissions*, never roles. A role is only a
named bundle of permissions, so adding a role means adding one entry to
ROLE_PERMISSIONS. The frontend receives the resolved permissions of the
current user from `GET /users/me` and never sees this mapping.

Actions every authenticated user may perform on their *own* data (profile,
password, own items) are not permissions: they are granted by ownership.
"""

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"


class Permission(StrEnum):
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_MANAGE = "users:manage"  # update or delete any user, assign roles
    METRICS_READ = "metrics:read"
    SETTINGS_MANAGE = "settings:manage"
    ITEMS_MANAGE_ALL = "items:manage_all"  # access items owned by other users


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.MANAGER: frozenset({Permission.USERS_READ, Permission.METRICS_READ}),
    Role.MEMBER: frozenset(),
}


def permissions_for(role: Role) -> frozenset[Permission]:
    return ROLE_PERMISSIONS[role]


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in permissions_for(role)
