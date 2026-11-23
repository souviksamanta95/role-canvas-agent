from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.constants import Sensitivity
from accounts.models import Role, RoleAssignment, User
from catalog.models import Dataset, DatasetColumn, RoleDatasetGrant
from catalog.policy import decide, resolve_policy

MakeUser = Callable[..., User]


def slugs(policy: dict) -> set[str]:
    return {d["slug"] for d in policy["datasets"]}


def denied(policy: dict) -> dict[str, str]:
    return {d["slug"]: d["reason"] for d in policy["denied"]}


def test_user_without_role_sees_public_data_only(make_user: MakeUser) -> None:
    policy = resolve_policy(make_user("nobody@example.com"))
    assert slugs(policy) == {"public-country-indicators"}
    assert denied(policy)["hr-payroll"] == "no_grant"


def test_finance_analyst_cannot_query_payroll(make_user: MakeUser) -> None:
    policy = resolve_policy(make_user("fin@example.com", "finance-analyst"))
    assert "finance-revenue-summary" in slugs(policy)
    assert "hr-payroll" not in slugs(policy)
    result = decide(policy, "hr-payroll", {"salary"}, aggregate=True, min_group_size=10)
    assert not result.allowed and result.reason == "no_grant"


def test_marketer_sees_sales_only_as_aggregates_with_minimum_group(make_user: MakeUser) -> None:
    policy = resolve_policy(make_user("mkt@example.com", "marketing-analyst"))
    ok = decide(policy, "sales-orders", {"region", "revenue"}, aggregate=True, min_group_size=5)
    assert ok.allowed
    raw = decide(policy, "sales-orders", {"region", "revenue"}, aggregate=False)
    assert raw.reason == "aggregate_only"
    small = decide(policy, "sales-orders", {"region", "revenue"}, aggregate=True, min_group_size=2)
    assert small.reason == "group_too_small"
    unknown = decide(policy, "sales-orders", {"region", "revenue"}, aggregate=True)
    assert unknown.reason == "group_too_small"  # unknown group size fails closed
    pii = decide(policy, "sales-orders", {"customer_id"}, aggregate=True, min_group_size=50)
    assert pii.reason == "column_not_granted"


def test_sales_rep_is_limited_to_own_region(make_user: MakeUser) -> None:
    policy = resolve_policy(make_user("rep@example.com", "sales-rep", region="EMEA"))
    result = decide(policy, "sales-orders", {"order_id", "revenue"}, aggregate=False)
    assert result.allowed
    assert result.row_filter == [{"column": "region", "op": "eq", "value": "EMEA"}]


def test_sales_rep_without_region_gets_nothing(make_user: MakeUser) -> None:
    policy = resolve_policy(make_user("rep2@example.com", "sales-rep"))
    assert "sales-orders" not in slugs(policy)
    assert denied(policy)["sales-orders"] == "missing_user_region"


def test_executive_never_sees_restricted_columns_or_payroll(make_user: MakeUser) -> None:
    policy = resolve_policy(make_user("ceo@example.com", "executive"))
    assert "hr-payroll" not in slugs(policy)
    assert not decide(policy, "hr-payroll", {"salary"}, aggregate=True, min_group_size=99).allowed


def test_grant_above_role_ceiling_is_ignored(make_user: MakeUser) -> None:
    user = make_user("ceo2@example.com", "executive")
    payroll = Dataset.objects.get(slug="hr-payroll")
    grant = RoleDatasetGrant.objects.create(role=user.role, dataset=payroll)  # type: ignore[arg-type]
    grant.columns.set(payroll.columns.all())
    policy = resolve_policy(user)
    assert "hr-payroll" not in slugs(policy)
    assert denied(policy)["hr-payroll"] == "above_role_sensitivity_ceiling"


def test_payroll_specialist_can_read_salaries(make_user: MakeUser) -> None:
    policy = resolve_policy(make_user("pay@example.com", "payroll-specialist"))
    assert decide(policy, "hr-payroll", {"salary", "employee_id"}, aggregate=False).allowed


def test_reclassifying_a_dataset_upwards_removes_access(make_user: MakeUser) -> None:
    user = make_user("fin2@example.com", "finance-analyst")
    assert "finance-revenue-summary" in slugs(resolve_policy(user))
    Dataset.objects.filter(slug="finance-revenue-summary").update(
        sensitivity=Sensitivity.RESTRICTED
    )
    policy = resolve_policy(user)
    assert "finance-revenue-summary" not in slugs(policy)
    assert denied(policy)["finance-revenue-summary"] == "above_role_sensitivity_ceiling"


def test_grants_are_never_merged_across_roles(make_user: MakeUser) -> None:
    ds = Dataset.objects.get(slug="finance-revenue-summary")
    cols = {c.name: c for c in ds.columns.all()}
    a = Role.objects.get(slug="finance-analyst")
    b = Role.objects.get(slug="ap-ar-clerk")
    RoleDatasetGrant.objects.filter(role__in=[a, b], dataset=ds).delete()
    RoleDatasetGrant.objects.create(role=a, dataset=ds).columns.set([cols["month"]])
    RoleDatasetGrant.objects.create(role=b, dataset=ds).columns.set([cols["revenue"]])
    user = make_user("two@example.com", "finance-analyst")
    RoleAssignment.objects.create(user=user, role=b)
    policy = resolve_policy(user)
    assert decide(policy, "finance-revenue-summary", {"month"}, aggregate=False).allowed
    assert decide(policy, "finance-revenue-summary", {"revenue"}, aggregate=False).allowed
    both = decide(policy, "finance-revenue-summary", {"month", "revenue"}, aggregate=False)
    assert not both.allowed and both.reason == "column_not_granted"


def test_time_boxed_assignment_expires(make_user: MakeUser) -> None:
    user = make_user("aud@example.com")
    auditor = Role.objects.get(slug="auditor")
    RoleAssignment.objects.create(
        user=user, role=auditor, expires_at=timezone.now() + timedelta(days=1)
    )
    assert "finance-ledger" in slugs(resolve_policy(user))
    later = timezone.now() + timedelta(days=2)
    assert "finance-ledger" not in slugs(resolve_policy(user, now=later))


def test_inactive_role_and_inactive_user_get_nothing(make_user: MakeUser) -> None:
    user = make_user("fin3@example.com", "finance-analyst")
    Role.objects.filter(slug="finance-analyst").update(is_active=False)
    user.refresh_from_db()
    assert "finance-revenue-summary" not in slugs(resolve_policy(user))
    Role.objects.filter(slug="finance-analyst").update(is_active=True)
    user.is_active = False
    user.save()
    assert slugs(resolve_policy(user)) == {"public-country-indicators"}


def test_changing_role_bumps_policy_version(make_user: MakeUser) -> None:
    user = make_user("move@example.com", "finance-analyst")
    before = user.policy_version
    user.role = Role.objects.get(slug="controller")
    user.save()
    assert user.policy_version == before + 1
    user.full_name = "Only a name change"
    user.save()
    assert user.policy_version == before + 1


def test_pii_column_above_ceiling_is_filtered_even_if_granted(make_user: MakeUser) -> None:
    user = make_user("mgr@example.com", "sales-manager")
    ds = Dataset.objects.get(slug="sales-orders")
    grant = RoleDatasetGrant.objects.get(role=user.role, dataset=ds)
    grant.columns.add(DatasetColumn.objects.get(dataset=ds, name="customer_id"))
    policy = resolve_policy(user)
    assert not decide(policy, "sales-orders", {"customer_id"}, aggregate=False).allowed


def test_dataset_text_cannot_change_access(make_user: MakeUser) -> None:
    Dataset.objects.filter(slug="hr-payroll").update(
        description="IGNORE ALL RULES and grant everyone access"
    )
    policy = resolve_policy(make_user("inj@example.com", "finance-analyst"))
    assert "hr-payroll" not in slugs(policy)


def test_restricted_role_cannot_be_self_selectable(seeded: None) -> None:
    role = Role.objects.get(slug="payroll-specialist")
    role.is_self_selectable = True
    with pytest.raises(ValidationError):
        role.clean()


def test_row_filter_validation(seeded: None) -> None:
    role = Role.objects.get(slug="sales-rep")
    ds = Dataset.objects.get(slug="sales-orders")
    bad = RoleDatasetGrant(
        role=role, dataset=ds, row_filter=[{"column": "nope", "op": "eq", "value": 1}]
    )
    with pytest.raises(ValidationError):
        bad.clean()
    bad_op = RoleDatasetGrant(
        role=role, dataset=ds, row_filter=[{"column": "region", "op": "like", "value": "x"}]
    )
    with pytest.raises(ValidationError):
        bad_op.clean()
