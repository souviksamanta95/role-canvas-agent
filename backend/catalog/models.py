from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from accounts.constants import Sensitivity
from accounts.models import Department, Role, User
from catalog.validators import (
    validate_identifier,
    validate_parquet_path,
    validate_row_filter,
)

# Schema that holds agent-queryable tables. The `public` schema holds only auth and RBAC.
AGENT_SCHEMA = "datasets"


class Dataset(models.Model):
    class Storage(models.TextChoices):
        POSTGRES = "postgres", "Postgres table (datasets schema)"
        PARQUET = "parquet", "Parquet file"

    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner_department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="datasets"
    )
    sensitivity = models.IntegerField(choices=Sensitivity.choices, default=Sensitivity.INTERNAL)
    storage_type = models.CharField(
        max_length=20, choices=Storage.choices, default=Storage.POSTGRES
    )
    location = models.CharField(
        max_length=300,
        help_text="Postgres: table name inside the datasets schema. "
        "Parquet: path relative to the data directory.",
    )
    source_url = models.URLField(blank=True)
    license_note = models.CharField(max_length=300, blank=True)
    row_limit = models.PositiveIntegerField(default=1000, help_text="Max rows returned per query.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        if self.storage_type == self.Storage.POSTGRES:
            validate_identifier(self.location)
        else:
            validate_parquet_path(self.location)


class DatasetColumn(models.Model):
    class DataType(models.TextChoices):
        STRING = "string"
        INTEGER = "integer"
        FLOAT = "float"
        DATE = "date"
        DATETIME = "datetime"
        BOOLEAN = "boolean"

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="columns")
    name = models.CharField(max_length=63, validators=[validate_identifier])
    data_type = models.CharField(max_length=20, choices=DataType.choices, default=DataType.STRING)
    description = models.CharField(max_length=300, blank=True)
    sensitivity = models.IntegerField(choices=Sensitivity.choices, default=Sensitivity.INTERNAL)
    is_pii = models.BooleanField(
        default=False, help_text="Personal data. Must be Confidential or higher."
    )

    class Meta:
        ordering = ["dataset__slug", "name"]
        constraints = [
            models.UniqueConstraint(fields=["dataset", "name"], name="uniq_column_per_dataset"),
        ]

    def __str__(self) -> str:
        return f"{self.dataset.slug}.{self.name}"

    def clean(self) -> None:
        if self.is_pii and self.sensitivity < Sensitivity.CONFIDENTIAL:
            raise ValidationError("PII columns must be Confidential or Restricted.")


class RoleDatasetGrant(models.Model):
    """What one role may do with one dataset. Everything not listed here is denied."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="dataset_grants")
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="grants")
    columns = models.ManyToManyField(
        DatasetColumn,
        blank=True,
        related_name="grants",
        help_text="Only these columns are visible.",
    )
    aggregate_only = models.BooleanField(
        default=False, help_text="Only aggregated results (sums, counts, averages), never raw rows."
    )
    min_group_size = models.PositiveSmallIntegerField(
        default=1,
        help_text="With aggregate-only: smallest number of rows allowed in any result group.",
    )
    row_filter = models.JSONField(
        default=list,
        blank=True,
        help_text='List of conditions ANDed together, e.g. [{"column": "region", "op": "eq", '
        '"value": "$user.region"}]. Operators: eq, neq, in, lt, lte, gt, gte.',
    )
    notes = models.CharField(max_length=300, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["role", "dataset"], name="uniq_grant_per_role_dataset"),
        ]

    def __str__(self) -> str:
        return f"{self.role} -> {self.dataset.slug}"

    def clean(self) -> None:
        if self.min_group_size < 1:
            raise ValidationError({"min_group_size": "Must be at least 1."})
        if self.dataset_id:
            names = set(self.dataset.columns.values_list("name", flat=True))
            validate_row_filter(self.row_filter, names)
        else:
            validate_row_filter(self.row_filter)


class AccessAuditLog(models.Model):
    """One row per access decision, for refusal accuracy and incident review."""

    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    user_email = models.EmailField(blank=True)
    dataset = models.ForeignKey(
        Dataset, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    allowed = models.BooleanField()
    reason = models.CharField(max_length=100, blank=True)
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{'ALLOW' if self.allowed else 'DENY'} {self.user_email} {self.reason}"
