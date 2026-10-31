"""Authorization tests: what each role may do over HTTP.

Mirrors the permission matrix in the README.
"""

import logging

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.core.permissions import Role
from tests.utils.user import create_random_user, create_user_token_headers
from tests.utils.utils import random_email, random_lower_string

API = settings.API_V1_STR


@pytest.fixture(scope="module")
def headers_by_role(client: TestClient, db: Session) -> dict[Role, dict[str, str]]:
    return {
        role: create_user_token_headers(client=client, db=db, role=role)
        for role in Role
    }


@pytest.mark.parametrize(
    ("role", "path", "expected_status"),
    [
        (Role.ADMIN, "/users/", 200),
        (Role.MANAGER, "/users/", 200),
        (Role.MEMBER, "/users/", 403),
        (Role.ADMIN, "/metrics/", 200),
        (Role.MANAGER, "/metrics/", 200),
        (Role.MEMBER, "/metrics/", 403),
    ],
)
def test_read_access_by_role(
    client: TestClient,
    headers_by_role: dict[Role, dict[str, str]],
    role: Role,
    path: str,
    expected_status: int,
) -> None:
    r = client.get(f"{API}{path}", headers=headers_by_role[role])
    assert r.status_code == expected_status


@pytest.mark.parametrize(
    ("role", "expected_status"),
    [(Role.ADMIN, 200), (Role.MANAGER, 403), (Role.MEMBER, 403)],
)
def test_only_admin_can_create_users(
    client: TestClient,
    headers_by_role: dict[Role, dict[str, str]],
    role: Role,
    expected_status: int,
) -> None:
    payload = {"email": random_email(), "password": random_lower_string()}
    r = client.post(f"{API}/users/", headers=headers_by_role[role], json=payload)
    assert r.status_code == expected_status


@pytest.mark.parametrize(
    ("role", "expected_status"),
    [(Role.ADMIN, 200), (Role.MANAGER, 403), (Role.MEMBER, 403)],
)
def test_only_admin_can_update_other_users(
    client: TestClient,
    db: Session,
    headers_by_role: dict[Role, dict[str, str]],
    role: Role,
    expected_status: int,
) -> None:
    other_user = create_random_user(db)
    r = client.patch(
        f"{API}/users/{other_user.id}",
        headers=headers_by_role[role],
        json={"full_name": "Changed by someone else"},
    )
    assert r.status_code == expected_status


@pytest.mark.parametrize("role", list(Role))
def test_every_role_can_update_own_profile(
    client: TestClient, headers_by_role: dict[Role, dict[str, str]], role: Role
) -> None:
    r = client.patch(
        f"{API}/users/me", headers=headers_by_role[role], json={"full_name": "Me"}
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "Me"


def test_member_cannot_escalate_own_role_via_profile_update(
    client: TestClient, headers_by_role: dict[Role, dict[str, str]]
) -> None:
    headers = headers_by_role[Role.MEMBER]
    client.patch(f"{API}/users/me", headers=headers, json={"role": "admin"})

    r = client.get(f"{API}/users/me", headers=headers)
    assert r.json()["role"] == "member"


def test_signup_always_creates_member(client: TestClient) -> None:
    payload = {
        "email": random_email(),
        "password": random_lower_string(),
        "role": "admin",
    }
    r = client.post(f"{API}/users/signup", json=payload)
    assert r.status_code == 200
    assert r.json()["role"] == "member"


def test_admin_cannot_change_own_role(
    client: TestClient, headers_by_role: dict[Role, dict[str, str]]
) -> None:
    headers = headers_by_role[Role.ADMIN]
    admin_id = client.get(f"{API}/users/me", headers=headers).json()["id"]

    r = client.patch(
        f"{API}/users/{admin_id}", headers=headers, json={"role": "member"}
    )
    assert r.status_code == 403


def test_current_user_exposes_permissions_of_role(
    client: TestClient, headers_by_role: dict[Role, dict[str, str]]
) -> None:
    r = client.get(f"{API}/users/me", headers=headers_by_role[Role.MANAGER])
    assert r.json()["permissions"] == ["metrics:read", "users:read"]


def test_denied_access_is_logged(
    client: TestClient,
    headers_by_role: dict[Role, dict[str, str]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING, logger="app.api.deps"):
        client.get(f"{API}/metrics/", headers=headers_by_role[Role.MEMBER])

    assert "Access denied" in caplog.text
    assert "permission=metrics:read" in caplog.text


def test_invalid_token_is_unauthorized_not_forbidden(client: TestClient) -> None:
    # The frontend logs the user out on 401 but keeps the session on 403.
    r = client.get(f"{API}/users/me", headers={"Authorization": "Bearer invalid"})
    assert r.status_code == 401
