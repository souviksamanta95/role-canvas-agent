"""Resolve what a user may access, and decide whether a requested query is allowed.

Rules (deny by default):
  * Public datasets are open to every signed-in user, public non-PII columns only.
  * Everything else needs a RoleDatasetGrant on one of the user's active roles.
  * A grant is ignored if the dataset is above the role's sensitivity ceiling.
  * Only columns listed in the grant AND at or below the ceiling are visible.
  * Grants are never merged. A query must fit entirely inside ONE grant, so two
    narrow grants cannot be combined into a wider one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from accounts.constants import Sensitivity
from accounts.models import User
from accounts.services import effective_roles
from catalog.models import Dataset, RoleDatasetGrant
from catalog.validators import USER_REGION


def _resolve_row_filter(
    row_filter: list[dict[str, Any]], user: User
) -> list[dict[str, Any]] | None:
    """Substitute user placeholders. Returns None if one cannot be filled (fail closed)."""
    resolved: list[dict[str, Any]] = []
    for cond in row_filter:
        value = cond["value"]
        if value == USER_REGION:
            if not user.region:
                return None
            value = user.region
        resolved.append({"column": cond["column"], "op": cond["op"], "value": value})
    return resolved


def resolve_policy(user: User, now: datetime | None = None) -> dict[str, Any]:
    roles = effective_roles(user, now)
    datasets = list(Dataset.objects.filter(is_active=True).prefetch_related("columns"))
    allowed: dict[str, dict[str, Any]] = {}
    denial: dict[str, str] = {}

    def entry(ds: Dataset) -> dict[str, Any]:
        return allowed.setdefault(
            ds.slug,
            {
                "slug": ds.slug,
                "name": ds.name,
                "description": ds.description,
                "sensitivity": Sensitivity(ds.sensitivity).label,
                "storage_type": ds.storage_type,
                "location": ds.location,
                "row_limit": ds.row_limit,
                "grants": [],
            },
        )

    # Baseline: public datasets, public non-PII columns, for every signed-in user.
    for ds in datasets:
        if ds.sensitivity == Sensitivity.PUBLIC:
            cols = sorted(
                c.name
                for c in ds.columns.all()
                if c.sensitivity == Sensitivity.PUBLIC and not c.is_pii
            )
            if cols:
                entry(ds)["grants"].append(
                    {
                        "role": None,
                        "columns": cols,
                        "row_filter": [],
                        "aggregate_only": False,
                        "min_group_size": 1,
                    }
                )

    grants = (
        RoleDatasetGrant.objects.filter(role__in=roles, dataset__is_active=True)
        .select_related("role", "dataset")
        .prefetch_related("columns")
    )
    for grant in grants:
        ds, role = grant.dataset, grant.role
        if ds.sensitivity > role.max_sensitivity:
            denial.setdefault(ds.slug, "above_role_sensitivity_ceiling")
            continue
        cols = sorted(
            c.name
            for c in grant.columns.all()
            if c.dataset_id == ds.pk and c.sensitivity <= role.max_sensitivity
        )
        if not cols:
            continue
        row_filter = _resolve_row_filter(grant.row_filter, user)
        if row_filter is None:
            denial.setdefault(ds.slug, "missing_user_region")
            continue
        entry(ds)["grants"].append(
            {
                "role": role.slug,
                "columns": cols,
                "row_filter": row_filter,
                "aggregate_only": grant.aggregate_only,
                "min_group_size": grant.min_group_size,
            }
        )

    denied = [
        {"slug": ds.slug, "name": ds.name, "reason": denial.get(ds.slug, "no_grant")}
        for ds in datasets
        if ds.slug not in allowed
    ]
    return {
        "user": {
            "id": user.pk,
            "email": user.email,
            "department": user.department.slug if user.department else None,
            "roles": [r.slug for r in roles],
        },
        "policy_version": user.policy_version,
        "datasets": sorted(allowed.values(), key=lambda d: d["slug"]),
        "denied": denied,
    }


@dataclass
class Decision:
    allowed: bool
    reason: str
    row_filter: list[dict[str, Any]] = field(default_factory=list)
    grant_role: str | None = None


def decide(
    policy: dict[str, Any],
    dataset_slug: str,
    columns: set[str],
    *,
    aggregate: bool,
    min_group_size: int | None = None,
) -> Decision:
    """Reference decision logic. The agent mirrors these rules before running any query.

    columns: every column the query reads (select, filter, group by, join keys).
    aggregate: True if the query returns only aggregated values.
    min_group_size: smallest group the query can produce, when known.
    """
    dataset = next((d for d in policy["datasets"] if d["slug"] == dataset_slug), None)
    if dataset is None:
        denied = next((d for d in policy["denied"] if d["slug"] == dataset_slug), None)
        return Decision(False, denied["reason"] if denied else "unknown_dataset")

    reason = "column_not_granted"
    for grant in dataset["grants"]:
        if not columns <= set(grant["columns"]):
            continue
        if grant["aggregate_only"]:
            if not aggregate:
                reason = "aggregate_only"
                continue
            if min_group_size is None or min_group_size < grant["min_group_size"]:
                reason = "group_too_small"
                continue
        return Decision(True, "allowed", grant["row_filter"], grant["role"])
    return Decision(False, reason)
