"""Verify a Google ID token sent by the frontend (Google Identity Services)."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


class GoogleAuthError(Exception):
    pass


class GoogleNotConfiguredError(GoogleAuthError):
    pass


def verify_google_id_token(token: str) -> dict[str, Any]:
    client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    if not client_id:
        raise GoogleNotConfiguredError("GOOGLE_OAUTH_CLIENT_ID is not set")
    try:
        claims: dict[str, Any] = id_token.verify_oauth2_token(
            token, google_requests.Request(), client_id
        )
    except ValueError as exc:
        raise GoogleAuthError("Invalid Google token") from exc
    if not claims.get("email_verified"):
        raise GoogleAuthError("Google email is not verified")
    allowed = settings.ALLOWED_EMAIL_DOMAINS
    domain = str(claims.get("email", "")).rsplit("@", 1)[-1].lower()
    if allowed and domain not in allowed:
        raise GoogleAuthError("Email domain is not allowed")
    return claims
