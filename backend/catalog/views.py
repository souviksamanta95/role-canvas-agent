from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from catalog.policy import resolve_policy


class MyAccessView(APIView):
    """What the signed-in user may query. Also the payload sent to the agent."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user: User = request.user  # type: ignore[assignment]
        return Response(resolve_policy(user))
