from django.utils import timezone
from django.db.models import Count
from django.core.cache import cache
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Poll, Option, Vote
from .serializers import (
    PollSerializer,
    CreatePollSerializer,
    VoteSerializer,
    AddOptionSerializer,
)
from .permissions import IsAdminOrReadOnly


class PollViewSet(viewsets.ModelViewSet):
    """
    Poll API:
    - GET    /polls/              → List available polls (non-expired)
    - POST   /polls/              → Create poll (admin only)
    - GET    /polls/{id}/         → Retrieve poll
    - POST   /polls/{id}/vote/    → Vote on a poll (authenticated)
    - POST   /polls/{id}/options/ → Add option to poll (admin only, before expiry)
    - GET    /polls/{id}/results/ → Poll results (cached 1 min)
    """

    queryset = Poll.objects.all().select_related("created_by").prefetch_related("options")
    permission_classes = [IsAdminOrReadOnly]

    # -------------------------------
    # Serializer selection
    # -------------------------------
    def get_serializer_class(self):
        if self.action == "create":
            return CreatePollSerializer
        if self.action == "vote":
            return VoteSerializer
        if self.action == "options":
            return AddOptionSerializer
        return PollSerializer

    # -------------------------------
    # Permissions per action
    # -------------------------------
    def get_permissions(self):
        if self.action in ["list", "retrieve", "results"]:
            return [permissions.AllowAny()]
        if self.action in ["vote"]:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    # -------------------------------
    # Querysets
    # -------------------------------
    def get_queryset(self):
        """
        For `list` → return only active polls (non-expired).
        For others → allow all polls.
        """
        qs = super().get_queryset()
        if self.action == "list":
            return qs.filter(expires_at__gt=timezone.now()).order_by("-created_at")
        return qs

    # -------------------------------
    # Actions
    # -------------------------------
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def vote(self, request, pk=None):
        """Vote on a poll (authenticated users only)."""
        poll = self.get_object()

        if poll.expires_at and poll.expires_at <= timezone.now():
            return Response(
                {"error": "This poll has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = VoteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(poll=poll)

        # Invalidate results cache
        cache.delete(f"poll_results:{poll.id}")

        return Response(
            {"message": "Vote recorded successfully."},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrReadOnly])
    def options(self, request, pk=None):
        """Allow admin to add new options to an existing poll."""
        poll = self.get_object()

        if poll.expires_at and poll.expires_at <= timezone.now():
            return Response(
                {"error": "This poll has expired, cannot add options."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AddOptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(poll=poll)

        # Invalidate results cache
        cache.delete(f"poll_results:{poll.id}")

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def results(self, request, pk=None):
        """Return poll results with caching (1 minute)."""
        cache_key = f"poll_results:{pk}"
        data = cache.get(cache_key)

        if not data:
            poll = self.get_object()

            # Annotate options with vote counts
            options = poll.options.annotate(votes_count=Count("votes"))

            poll_data = PollSerializer(poll).data
            total_votes = sum(opt.votes_count for opt in options)

            data = {
                "poll": poll_data,
                "total_votes": total_votes,
                "options": [
                    {"id": opt.id, "text": opt.text, "votes_count": opt.votes_count}
                    for opt in options
                ],
            }
            cache.set(cache_key, data, timeout=60)  # Cache for 1 minute

        return Response(data)
