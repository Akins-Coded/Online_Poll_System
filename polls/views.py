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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    # -------------------------------
    # Permissions per action
    # -------------------------------
    def get_permissions(self):
        if self.action in ["list", "retrieve", "results"]:
            return [permissions.AllowAny()]
        if self.action == "vote":
            return [permissions.IsAuthenticated()]
        return [IsAdminOrReadOnly()]

    # -------------------------------
    # Querysets
    # -------------------------------
    def get_queryset(self):
        """
        - For list → return only active polls.
        - Always annotate votes_count for each option.
        """
        qs = super().get_queryset()

        # Prefetch options with votes_count annotated
        qs = qs.prefetch_related(
            models.Prefetch(
                "options",
                queryset=Option.objects.annotate(votes_count=Count("votes")),
            )
        )

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
            return Response({"error": "This poll has expired."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Invalidate results cache
        cache.delete(f"poll_results:{poll.id}")

        return Response({"message": "Vote recorded successfully."}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrReadOnly])
    def options(self, request, pk=None):
        """Allow admin to add new options to an existing poll."""
        poll = self.get_object()

        if poll.expires_at and poll.expires_at <= timezone.now():
            return Response({"error": "This poll has expired, cannot add options."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
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
            poll_data = PollSerializer(poll).data
            total_votes = sum(opt["votes_count"] for opt in poll_data["options"])

            data = {
                "poll": poll_data,
                "total_votes": total_votes,
                "options": poll_data["options"],
            }
            cache.set(cache_key, data, timeout=60)

        return Response(data)
