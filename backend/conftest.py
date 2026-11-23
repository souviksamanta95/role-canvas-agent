from __future__ import annotations

from collections.abc import Callable

import pytest
from django.core.management import call_command

from accounts.models import Role, User


@pytest.fixture
def seeded(db: None) -> None:
    call_command("seed_access")


@pytest.fixture
def make_user(seeded: None) -> Callable[..., User]:
    def _make(email: str, role: str | None = None, region: str = "") -> User:
        user = User.objects.create_user(email=email, region=region)
        if role:
            r = Role.objects.get(slug=role)
            user.department, user.role = r.department, r
            user.save()
        return user

    return _make
