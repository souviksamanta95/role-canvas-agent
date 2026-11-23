from __future__ import annotations

from typing import Any

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from accounts.models import Department, Role, RoleAssignment, User


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "department", "max_sensitivity", "is_self_selectable", "is_active"]
    list_filter = ["department", "max_sensitivity", "is_self_selectable", "is_active"]
    search_fields = ["name", "department__name"]
    prepopulated_fields = {"slug": ("name",)}
    actions = ["duplicate_roles"]

    @admin.action(description="Duplicate selected roles (with their data grants)")
    def duplicate_roles(self, request: HttpRequest, queryset: QuerySet[Role]) -> None:
        for role in queryset:
            grants = list(role.dataset_grants.prefetch_related("columns"))
            role.pk = None
            role.name = f"{role.name} (copy)"
            role.slug = f"{role.slug}-copy"
            role.is_self_selectable = False  # a copy must be reviewed before users can pick it
            role.save()
            for grant in grants:
                columns = list(grant.columns.all())
                grant.pk = None
                grant.role = role
                grant.save()
                grant.columns.set(columns)
        self.message_user(request, "Roles duplicated as non-self-selectable.", messages.SUCCESS)


class RoleAssignmentInline(admin.TabularInline):
    model = RoleAssignment
    fk_name = "user"
    extra = 0
    autocomplete_fields = ["role"]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["email", "full_name", "department", "role", "is_active", "is_staff"]
    list_filter = ["department", "role", "is_active", "is_staff"]
    search_fields = ["email", "full_name"]
    readonly_fields = ["google_sub", "last_login", "date_joined", "policy_version"]
    inlines = [RoleAssignmentInline]
    fieldsets = [
        (None, {"fields": ["email", "full_name", "picture_url", "google_sub"]}),
        ("Access", {"fields": ["department", "role", "region", "policy_version"]}),
        (
            "Status",
            {"fields": ["is_active", "is_staff", "is_superuser", "last_login", "date_joined"]},
        ),
        ("Admin permissions", {"classes": ["collapse"], "fields": ["groups", "user_permissions"]}),
    ]

    def save_formset(self, request: HttpRequest, form: Any, formset: Any, change: bool) -> None:
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for obj in instances:
            if isinstance(obj, RoleAssignment) and obj.granted_by_id is None:
                obj.granted_by = request.user  # type: ignore[assignment]
            obj.save()
        formset.save_m2m()
        form.instance.bump_policy_version()  # role assignments changed: invalidate old tokens


admin.site.site_header = "RoleCanvas administration"
