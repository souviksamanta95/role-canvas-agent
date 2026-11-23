from __future__ import annotations

from typing import Any

from rest_framework import serializers

from accounts.models import Department, Role, User


class RoleSerializer(serializers.ModelSerializer[Role]):
    class Meta:
        model = Role
        fields = ["slug", "name", "description"]


class DepartmentSerializer(serializers.ModelSerializer[Department]):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ["slug", "name", "description", "roles"]

    def get_roles(self, obj: Department) -> list[dict[str, Any]]:
        """Only roles a user may pick for themselves appear in the dropdown."""
        roles = obj.roles.filter(is_active=True, is_self_selectable=True)
        return list(RoleSerializer(roles, many=True).data)


class UserSerializer(serializers.ModelSerializer[User]):
    department = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    role = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    needs_onboarding = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "picture_url",
            "department",
            "role",
            "region",
            "needs_onboarding",
        ]
        read_only_fields = fields


class ProfileUpdateSerializer(serializers.Serializer[Any]):
    """Self-service profile change: department first, then a role inside that department."""

    department = serializers.SlugField(required=False)
    role = serializers.SlugField(required=False)
    region = serializers.CharField(required=False, allow_blank=True, max_length=50)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        user: User = self.context["user"]
        department = user.department
        if "department" in attrs:
            department = Department.objects.filter(slug=attrs["department"], is_active=True).first()
            if department is None:
                raise serializers.ValidationError({"department": "Unknown department."})
        attrs["_department"] = department

        role = user.role
        if "role" in attrs:
            if department is None:
                raise serializers.ValidationError({"role": "Choose a department first."})
            role = Role.objects.filter(
                department=department,
                slug=attrs["role"],
                is_active=True,
                is_self_selectable=True,
            ).first()
            if role is None:
                raise serializers.ValidationError(
                    {
                        "role": "Unknown role for this department, or it needs administrator approval."
                    }
                )
        elif "department" in attrs and (role is None or role.department_id != department.pk):  # type: ignore[union-attr]
            role = None  # moved department without picking a role: onboarding again
        attrs["_role"] = role
        return attrs
