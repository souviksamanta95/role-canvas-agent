from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.google import GoogleAuthError, GoogleNotConfiguredError, verify_google_id_token
from accounts.models import Department, User
from accounts.serializers import DepartmentSerializer, ProfileUpdateSerializer, UserSerializer
from accounts.tokens import issue_tokens

UserModel = get_user_model()


class _AuthThrottled(APIView):
    throttle_scope = "auth"
    permission_classes = [AllowAny]
    authentication_classes: list[type] = []


class GoogleLoginView(_AuthThrottled):
    """Exchange a Google ID token for our own JWT pair. The only way normal users sign in."""

    def post(self, request: Request) -> Response:
        token = request.data.get("id_token")
        if not isinstance(token, str) or not token:
            return Response({"detail": "id_token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            claims = verify_google_id_token(token)
        except GoogleNotConfiguredError:
            return Response(
                {"detail": "Google sign-in is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except GoogleAuthError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        email = str(claims["email"]).lower()
        with transaction.atomic():
            user = (
                User.objects.filter(google_sub=claims["sub"]).first()
                or User.objects.filter(email=email).first()
            )
            if user is None:
                user = User.objects.create_user(email=email, google_sub=claims["sub"])
            if not user.is_active:
                return Response({"detail": "Account disabled."}, status=status.HTTP_403_FORBIDDEN)
            user.google_sub = claims["sub"]
            user.full_name = str(claims.get("name", user.full_name))[:200]
            user.picture_url = str(claims.get("picture", user.picture_url))[:500]
            user.last_login = timezone.now()
            user.save()
        return Response({**issue_tokens(user), "user": UserSerializer(user).data})


class RefreshView(_AuthThrottled):
    """Rotate a refresh token. Fresh claims are minted from the database every time."""

    def post(self, request: Request) -> Response:
        raw = request.data.get("refresh")
        try:
            refresh = RefreshToken(raw)  # type: ignore[arg-type]
            user = User.objects.get(pk=refresh["user_id"])
        except (TokenError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED
            )
        if not user.is_active:
            return Response({"detail": "Account disabled."}, status=status.HTTP_403_FORBIDDEN)
        try:
            refresh.blacklist()
        except AttributeError:
            pass
        return Response(issue_tokens(user))


class LogoutView(_AuthThrottled):
    def post(self, request: Request) -> Response:
        try:
            RefreshToken(request.data.get("refresh")).blacklist()  # type: ignore[arg-type]
        except TokenError:
            pass  # already invalid: the goal (no usable token) is met
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(UserSerializer(request.user).data)

    def patch(self, request: Request) -> Response:
        user: User = request.user  # type: ignore[assignment]
        serializer = ProfileUpdateSerializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user.department = data["_department"]
        user.role = data["_role"]
        if "region" in data:
            user.region = data["region"]
        user.save()  # bumps policy_version when department, role or region changed
        # Old access tokens are now stale, so hand back a fresh pair.
        return Response({**issue_tokens(user), "user": UserSerializer(user).data})


class DepartmentListView(APIView):
    """Feeds the onboarding/profile dropdowns: departments, each with its pickable roles."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        departments = Department.objects.filter(is_active=True).prefetch_related("roles")
        return Response(DepartmentSerializer(departments, many=True).data)
