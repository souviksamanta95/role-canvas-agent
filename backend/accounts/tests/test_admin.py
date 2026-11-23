from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import Role, User
from catalog.models import Dataset, RoleDatasetGrant


@pytest.fixture
def admin_client(seeded: None) -> Client:
    admin = User.objects.create_superuser("admin@example.com", "pw-for-tests")
    client = Client()
    client.force_login(admin)
    return client


@pytest.mark.parametrize(
    "name",
    [
        "admin:accounts_department_changelist",
        "admin:accounts_role_changelist",
        "admin:accounts_user_changelist",
        "admin:catalog_dataset_changelist",
        "admin:catalog_roledatasetgrant_changelist",
        "admin:catalog_roledatasetgrant_add",
        "admin:catalog_accessauditlog_changelist",
    ],
)
def test_admin_pages_render(admin_client: Client, name: str) -> None:
    assert admin_client.get(reverse(name)).status_code == 200


def test_role_page_shows_grants_inline(admin_client: Client) -> None:
    role = Role.objects.get(slug="sales-rep")
    response = admin_client.get(reverse("admin:accounts_role_change", args=[role.pk]))
    assert response.status_code == 200
    assert b"dataset_grants" in response.content


def test_user_change_page_renders(admin_client: Client) -> None:
    user = User.objects.get(email="admin@example.com")
    assert (
        admin_client.get(reverse("admin:accounts_user_change", args=[user.pk])).status_code == 200
    )


def test_grant_change_page_limits_columns_to_dataset(admin_client: Client) -> None:
    grant = RoleDatasetGrant.objects.filter(
        dataset=Dataset.objects.get(slug="sales-orders")
    ).first()
    assert grant is not None
    response = admin_client.get(reverse("admin:catalog_roledatasetgrant_change", args=[grant.pk]))
    assert response.status_code == 200
    assert (
        b"finance_ledger" not in response.content
        and b"finance-ledger.amount" not in response.content
    )


def test_duplicate_role_action_creates_locked_copy(admin_client: Client) -> None:
    role = Role.objects.get(slug="controller")
    response = admin_client.post(
        reverse("admin:accounts_role_changelist"),
        {"action": "duplicate_roles", "_selected_action": [role.pk]},
    )
    assert response.status_code == 302
    copy = Role.objects.get(slug="controller-copy")
    assert copy.is_self_selectable is False
    assert copy.dataset_grants.count() == role.dataset_grants.count()
