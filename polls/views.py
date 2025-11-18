# views.py
from django.utils import timezone
from django.db.models import Count, Prefetch
from django.core.cache import cache
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Poll, Option
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

    - Anyone:
        * list active polls
        * retrieve a single poll
        * view poll results

    - Authenticated users:
        * vote on active polls

    - Admins only (via IsAdminOrReadOnly):
        * create polls
        * update / delete polls
        * add options to polls
    """

    queryset = (
        Poll.objects.all()
        .select_related("created_by")
        .prefetch_related("options")
    )
    serializer_class = PollSerializer
    permission_classes = (IsAdminOrReadOnly,)

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
        # Public read-only endpoints
        if self.action in ("list", "retrieve", "results"):
            return (permissions.AllowAny(),)

        # Any authenticated user can vote
        if self.action == "vote":
            return (permissions.IsAuthenticated(),)

        # create / update / partial_update / destroy / options → admins only
        return (IsAdminOrReadOnly(),)

    # -------------------------------
    # Querysets
    # -------------------------------
    def get_queryset(self):
        """
        - For list → return only non-expired polls.
        - Annotate each option with votes_count.
        - Annotate each poll with total_votes.
        """
        qs = (
            Poll.objects.select_related("created_by")
            .prefetch_related(
                Prefetch(
                    "options",
                    queryset=Option.objects.annotate(
                        votes_count=Count("votes")
                    ),
                )
            )
            .annotate(total_votes=Count("votes"))
            .order_by("-created_at")
        )

        if self.action == "list":
            qs = qs.filter(expires_at__gt=timezone.now())

        return qs

    # -------------------------------
    # Actions
    # -------------------------------
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def vote(self, request, pk=None):
        """Vote on a poll (authenticated users only)."""
        poll = self.get_object()

        if poll.expires_at and poll.expires_at <= timezone.now():
            return Response(
                {"error": "This poll has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Invalidate results cache
        cache.delete(f"poll_results:{poll.id}")

        return Response(
            {"message": "Vote recorded successfully."},
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminOrReadOnly],
    )
    def options(self, request, pk=None):
        """Allow admin to add new options to an existing poll."""
        poll = self.get_object()

        if poll.expires_at and poll.expires_at <= timezone.now():
            return Response(
                {"error": "This poll has expired, cannot add options."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(poll=poll)

        # Invalidate results cache
        cache.delete(f"poll_results:{poll.id}")

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.AllowAny],
    )
    def results(self, request, pk=None):
        """Public endpoint: returns cached poll results."""
        cache_key = f"poll_results:{pk}"

        def fetch():
            poll = self.get_object()
            poll_data = PollSerializer(poll).data
            return {
                "poll": poll_data,
                "total_votes": poll.total_votes,
                "options": poll_data["options"],
            }

        data = cache.get_or_set(cache_key, fetch, timeout=60)
        return Response(data)
