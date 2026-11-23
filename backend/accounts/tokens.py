"""JWT issuing. Tokens carry `pv` (policy version); a stale `pv` is rejected."""

from __future__ import annotations

from typing import cast

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken, Token

from accounts.models import User


def issue_tokens(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    # Informational claims for the frontend. Authorization never trusts them: it is
    # always recomputed from the database.
    refresh["pv"] = user.policy_version
    refresh["email"] = user.email
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class PolicyVersionJWTAuthentication(JWTAuthentication):
    """Rejects access tokens issued before the user's department/role last changed."""

    def get_user(self, validated_token: Token) -> User:
        user = cast(User, super().get_user(validated_token))
        if validated_token.get("pv") != user.policy_version:
            raise AuthenticationFailed("Token is stale. Refresh it.", code="token_stale")
        return user
