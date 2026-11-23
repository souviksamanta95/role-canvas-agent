from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.constants import Sensitivity


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Role(models.Model):
    """A named bundle of data grants that belongs to exactly one department.

    max_sensitivity is a hard ceiling: a grant on data above it is ignored.
    Roles that are not self-selectable can only be assigned by an administrator.
    """

    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="roles")
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    max_sensitivity = models.IntegerField(choices=Sensitivity.choices, default=Sensitivity.INTERNAL)
    is_self_selectable = models.BooleanField(
        default=True,
        help_text="Users may pick this role themselves in their profile. "
        "Untick for sensitive roles that an administrator must assign.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["department__name", "name"]
        constraints = [
            models.UniqueConstraint(fields=["department", "slug"], name="uniq_role_slug_per_dept"),
        ]

    def __str__(self) -> str:
        return f"{self.department.name} / {self.name}"

    def clean(self) -> None:
        if self.is_self_selectable and self.max_sensitivity >= Sensitivity.RESTRICTED:
            raise ValidationError(
                "A role with a Restricted ceiling cannot be self-selectable. "
                "Untick 'is self selectable' so an administrator assigns it."
            )


class UserManager(BaseUserManager["User"]):
    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra: Any) -> User:
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()  # Google-only users never have a password
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra: Any) -> User:
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if not password:
            raise ValueError("Superusers need a password to sign in to the admin")
        return self.create_user(email, password, **extra)


# Fields whose change invalidates previously issued access tokens.
_POLICY_FIELDS = ("department_id", "role_id", "region", "is_active")


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200, blank=True)
    picture_url = models.URLField(max_length=500, blank=True)
    google_sub = models.CharField(max_length=64, unique=True, null=True, blank=True)

    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )
    role = models.ForeignKey(
        Role, null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )
    region = models.CharField(
        max_length=50,
        blank=True,
        help_text="Used by row filters that reference $user.region (for example sales reps).",
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    policy_version = models.PositiveIntegerField(
        default=1,
        help_text="Bumped when department, role or region change. Invalidates old tokens.",
    )

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:
        return self.email

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.email = self.email.lower()
        if self.pk:
            old = User.objects.filter(pk=self.pk).values(*_POLICY_FIELDS).first()
            if old and any(old[f] != getattr(self, f) for f in _POLICY_FIELDS):
                self.policy_version += 1
        super().save(*args, **kwargs)

    def bump_policy_version(self) -> None:
        User.objects.filter(pk=self.pk).update(policy_version=models.F("policy_version") + 1)
        self.refresh_from_db(fields=["policy_version"])

    @property
    def needs_onboarding(self) -> bool:
        return self.role_id is None


class RoleAssignment(models.Model):
    """Extra role granted to a user by an administrator, optionally time-boxed."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="role_assignments")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="assignments")
    granted_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Leave empty for no expiry.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="uniq_role_assignment"),
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.role}"

    def is_current(self, now: Any = None) -> bool:
        now = now or timezone.now()
        return self.expires_at is None or self.expires_at > now
