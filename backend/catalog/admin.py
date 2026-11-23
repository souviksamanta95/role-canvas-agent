from __future__ import annotations

from typing import Any

from django import forms
from django.contrib import admin
from django.http import HttpRequest

from catalog.models import AccessAuditLog, Dataset, DatasetColumn, RoleDatasetGrant


class DatasetColumnInline(admin.TabularInline):
    model = DatasetColumn
    extra = 0


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "owner_department",
        "sensitivity",
        "storage_type",
        "location",
        "is_active",
    ]
    list_filter = ["owner_department", "sensitivity", "storage_type", "is_active"]
    search_fields = ["name", "slug", "location"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [DatasetColumnInline]


class GrantForm(forms.ModelForm):  # type: ignore[type-arg]
    class Meta:
        model = RoleDatasetGrant
        fields = "__all__"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        dataset_id = self.instance.dataset_id if self.instance.pk else None
        if dataset_id:
            self.fields["columns"].queryset = DatasetColumn.objects.filter(dataset_id=dataset_id)

    def clean(self) -> dict[str, Any]:
        cleaned: dict[str, Any] = super().clean() or {}
        dataset, columns = cleaned.get("dataset"), cleaned.get("columns")
        if dataset and columns:
            wrong = [str(c) for c in columns if c.dataset_id != dataset.pk]
            if wrong:
                raise forms.ValidationError(f"Columns not in {dataset.slug}: {', '.join(wrong)}")
        return cleaned


class GrantInline(admin.StackedInline):
    model = RoleDatasetGrant
    form = GrantForm
    extra = 0
    filter_horizontal = ["columns"]
    autocomplete_fields = ["dataset"]


@admin.register(RoleDatasetGrant)
class RoleDatasetGrantAdmin(admin.ModelAdmin):
    """Pick role and dataset, save, then reopen to choose columns from that dataset only."""

    form = GrantForm
    list_display = ["role", "dataset", "aggregate_only", "min_group_size"]
    list_filter = ["role__department", "dataset", "aggregate_only"]
    filter_horizontal = ["columns"]


@admin.register(AccessAuditLog)
class AccessAuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "user_email", "dataset", "allowed", "reason"]
    list_filter = ["allowed", "reason"]
    search_fields = ["user_email"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


# Edit a role's data grants directly on the role page.
from accounts.admin import RoleAdmin  # noqa: E402

RoleAdmin.inlines = [GrantInline]
