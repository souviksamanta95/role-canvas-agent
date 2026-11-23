"""Business rules for who has which roles."""

from __future__ import annotations

from datetime import datetime

from django.utils import timezone

from accounts.models import Role, User


def effective_roles(user: User, now: datetime | None = None) -> list[Role]:
    """Active roles a user holds right now: their own role plus unexpired admin assignments."""
    now = now or timezone.now()
    if not user.is_active:
        return []
    roles: dict[int, Role] = {}
    if user.role_id and user.role is not None and user.role.is_active:
        roles[user.role.pk] = user.role
    for assignment in user.role_assignments.select_related("role").all():
        if assignment.role.is_active and assignment.is_current(now):
            roles[assignment.role.pk] = assignment.role
    return list(roles.values())
