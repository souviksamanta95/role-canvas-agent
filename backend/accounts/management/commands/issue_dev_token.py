"""Issue a JWT pair for a user without Google. DEVELOPMENT ONLY: refuses unless DEBUG is on."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from accounts.tokens import issue_tokens


class Command(BaseCommand):
    help = "Issue a JWT pair for EMAIL (created if missing). Only works when DJANGO_DEBUG=True."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("email")

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.DEBUG:
            raise CommandError("issue_dev_token only runs with DJANGO_DEBUG=True.")
        user = User.objects.filter(
            email=options["email"].lower()
        ).first() or User.objects.create_user(options["email"])
        tokens = issue_tokens(user)
        self.stdout.write(f"access:  {tokens['access']}")
        self.stdout.write(f"refresh: {tokens['refresh']}")
