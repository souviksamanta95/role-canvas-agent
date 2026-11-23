from __future__ import annotations

from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from rest_framework.test import APIClient

from accounts.google import GoogleAuthError
from accounts.models import User

GOOGLE = {
    "sub": "g-123",
    "email": "Jane@Example.com",
    "email_verified": True,
    "name": "Jane",
    "picture": "",
}


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def login(client: APIClient, claims: dict | None = None) -> dict:
    with patch("accounts.views.verify_google_id_token", return_value=claims or GOOGLE):
        response = client.post("/api/auth/google/", {"id_token": "x"}, format="json")
    assert response.status_code == 200, response.content
    return dict(response.json())


def auth(client: APIClient, tokens: dict) -> None:
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")


def test_health_is_public(client: APIClient) -> None:
    assert client.get("/health/").status_code == 200


def test_api_requires_a_token(client: APIClient, seeded: None) -> None:
    assert client.get("/api/me/").status_code == 401
    assert client.get("/api/departments/").status_code == 401
    assert client.get("/api/me/access/").status_code == 401


def test_first_google_login_creates_user_needing_onboarding(
    client: APIClient, seeded: None
) -> None:
    tokens = login(client)
    assert tokens["user"]["email"] == "jane@example.com"
    assert tokens["user"]["needs_onboarding"] is True
    user = User.objects.get(email="jane@example.com")
    assert not user.has_usable_password()


def test_invalid_google_token_is_rejected(client: APIClient, seeded: None) -> None:
    with patch("accounts.views.verify_google_id_token", side_effect=GoogleAuthError("bad")):
        response = client.post("/api/auth/google/", {"id_token": "x"}, format="json")
    assert response.status_code == 401
    assert client.post("/api/auth/google/", {}, format="json").status_code == 400


def test_google_sign_in_unconfigured_returns_503(client: APIClient, seeded: None) -> None:
    with override_settings(GOOGLE_OAUTH_CLIENT_ID=""):
        response = client.post("/api/auth/google/", {"id_token": "x"}, format="json")
    assert response.status_code == 503


def test_domain_allow_list_is_enforced() -> None:
    from accounts.google import verify_google_id_token

    claims = {"email": "eve@evil.com", "email_verified": True}
    with (
        override_settings(ALLOWED_EMAIL_DOMAINS=["example.com"]),
        patch("accounts.google.id_token.verify_oauth2_token", return_value=claims),
        pytest.raises(GoogleAuthError),
    ):
        verify_google_id_token("x")
    unverified = {"email": "a@example.com", "email_verified": False}
    with (
        patch("accounts.google.id_token.verify_oauth2_token", return_value=unverified),
        pytest.raises(GoogleAuthError),
    ):
        verify_google_id_token("x")


def test_onboarding_picks_department_then_role(client: APIClient, seeded: None) -> None:
    tokens = login(client)
    auth(client, tokens)
    departments = client.get("/api/departments/").json()
    finance = next(d for d in departments if d["slug"] == "finance")
    role_slugs = {r["slug"] for r in finance["roles"]}
    assert "finance-analyst" in role_slugs
    assert "auditor" not in role_slugs  # admin-assigned roles are not offered

    response = client.patch(
        "/api/me/", {"department": "finance", "role": "finance-analyst"}, format="json"
    )
    assert response.status_code == 200
    assert response.json()["user"]["needs_onboarding"] is False
    auth(client, response.json())
    access = client.get("/api/me/access/").json()
    assert "finance-revenue-summary" in {d["slug"] for d in access["datasets"]}


def test_role_must_belong_to_chosen_department(client: APIClient, seeded: None) -> None:
    auth(client, login(client))
    response = client.patch(
        "/api/me/", {"department": "marketing", "role": "controller"}, format="json"
    )
    assert response.status_code == 400
    assert client.patch("/api/me/", {"role": "finance-analyst"}, format="json").status_code == 400


def test_user_cannot_self_assign_admin_only_roles(client: APIClient, seeded: None) -> None:
    auth(client, login(client))
    for dept, role in [
        ("finance", "auditor"),
        ("hr", "payroll-specialist"),
        ("general", "platform-admin"),
    ]:
        response = client.patch("/api/me/", {"department": dept, "role": role}, format="json")
        assert response.status_code == 400, role


def test_changing_department_clears_role(client: APIClient, seeded: None) -> None:
    tokens = login(client)
    auth(client, tokens)
    client.patch("/api/me/", {"department": "finance", "role": "finance-analyst"}, format="json")
    user = User.objects.get(email="jane@example.com")
    assert user.role is not None
    auth(client, login(client))
    response = client.patch("/api/me/", {"department": "marketing"}, format="json")
    assert response.json()["user"]["role"] is None
    assert response.json()["user"]["needs_onboarding"] is True


def test_old_access_token_is_rejected_after_role_change(client: APIClient, seeded: None) -> None:
    old = login(client)
    auth(client, old)
    new = client.patch(
        "/api/me/", {"department": "finance", "role": "finance-analyst"}, format="json"
    ).json()
    auth(client, old)
    assert client.get("/api/me/").status_code == 401  # stale policy version
    auth(client, new)
    assert client.get("/api/me/").status_code == 200


def test_admin_side_role_change_invalidates_tokens_and_refresh_recovers(
    client: APIClient, seeded: None
) -> None:
    from accounts.models import Role

    tokens = login(client)
    user = User.objects.get(email="jane@example.com")
    user.role = Role.objects.get(slug="controller")
    user.department = user.role.department
    user.save()  # what the admin does
    auth(client, tokens)
    assert client.get("/api/me/").status_code == 401
    client.credentials()
    refreshed = client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert refreshed.status_code == 200
    auth(client, refreshed.json())
    assert client.get("/api/me/").status_code == 200


def test_refresh_token_is_single_use_and_logout_revokes(client: APIClient, seeded: None) -> None:
    tokens = login(client)
    first = client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert first.status_code == 200
    again = client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert again.status_code == 401
    assert (
        client.post(
            "/api/auth/logout/", {"refresh": first.json()["refresh"]}, format="json"
        ).status_code
        == 204
    )
    revoked = client.post("/api/auth/refresh/", {"refresh": first.json()["refresh"]}, format="json")
    assert revoked.status_code == 401


def test_disabled_user_cannot_refresh(client: APIClient, seeded: None) -> None:
    tokens = login(client)
    User.objects.filter(email="jane@example.com").update(is_active=False)
    response = client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert response.status_code == 403


@override_settings(DEBUG=False)
def test_dev_token_command_refuses_outside_debug(db: None) -> None:
    with pytest.raises(CommandError):
        call_command("issue_dev_token", "x@example.com")
