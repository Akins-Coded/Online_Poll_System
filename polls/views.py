from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils import timezone
from django.core.cache import cache

from .models import Poll, Option, Vote
from .serializers import (
    PollSerializer,
    CreatePollSerializer,
    AddOptionSerializer,
    VoteSerializer,
)
from .permissions import IsAdminOrReadOnly


class PollViewSet(viewsets.ModelViewSet):
    """Poll API with unified caching for results, per-user votes, and paginated list."""

    POLL_RESULTS_TIMEOUT = 30  # seconds
    POLL_LIST_TIMEOUT = 300  # seconds (5 minutes)
    
    queryset = Poll.objects.all().select_related("created_by").prefetch_related("options").order_by("-created_at")
    serializer_class = PollSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    # -----------------------------
    # Cache key helpers
    # -----------------------------
    @staticmethod
    def poll_results_cache_key(poll_id: int) -> str:
        return f"poll_results:{poll_id}"

    @staticmethod
    def user_vote_cache_key(poll_id: int, user_id: int) -> str:
        return f"user_vote:{poll_id}:{user_id}"

    @staticmethod
    def poll_list_cache_key(page: int) -> str:
        return f"poll_list:page:{page}"

    # -----------------------------
    # Helper to DRY cache get/set
    # -----------------------------
    def get_or_set_cache(self, key: str, fetch_func, timeout: int):
        data = cache.get(key)
        if data is None:
            data = fetch_func()
            cache.set(key, data, timeout=timeout)
        return data

    # -----------------------------
    # Serializers
    # -----------------------------
    def get_serializer_class(self):
        if self.action == "create":
            return CreatePollSerializer
        return PollSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        # Optional: Invalidate poll list cache on new poll
        cache.clear()  # Or selectively delete poll_list cache if needed

    # -----------------------------
    # Actions
    # -----------------------------
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrReadOnly])
    def options(self, request, pk=None):
        """Add option to a poll"""
        poll = self.get_object()
        if timezone.now() >= poll.expires_at:
            return Response({"detail": "Poll expired."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AddOptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(poll=poll)
            # Invalidate poll results cache when options change
            cache.delete(self.poll_results_cache_key(poll.id))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        poll = self.get_object()
        serializer = VoteSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            vote = serializer.save()
            # Invalidate poll results cache
            cache.delete(self.poll_results_cache_key(poll.id))
            # Cache per-user vote
            if request.user.is_authenticated:
                cache.set(
                    self.user_vote_cache_key(poll.id, request.user.id),
                    vote.option.id,
                    timeout=self.POLL_RESULTS_TIMEOUT
                )
            return Response({"detail": "Vote cast successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def results(self, request, pk=None):
        poll = self.get_object()
        cache_key = self.poll_results_cache_key(poll.id)
        user_vote_key = self.user_vote_cache_key(poll.id, request.user.id) if request.user.is_authenticated else None

        def fetch_results():
            results_qs = (
                Option.objects.filter(poll=poll)
                .annotate(vote_count=Count("votes"))
                .values("id", "text", "vote_count")
            )
            total_votes = sum(r["vote_count"] for r in results_qs)
            return {
                "poll_id": poll.id,
                "title": poll.title,
                "description": poll.description,
                "total_votes": total_votes,
                "results": list(results_qs),
            }

        data = self.get_or_set_cache(cache_key, fetch_results, self.POLL_RESULTS_TIMEOUT)

        if user_vote_key:
            data["user_vote"] = cache.get(user_vote_key, None)

        return Response(data)

    # -----------------------------
    # Paginated list with caching
    # -----------------------------
    @method_decorator(cache_page(POLL_LIST_TIMEOUT))
    def list(self, request, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        cache_key = self.poll_list_cache_key(page_number)

        def fetch_page():
            page = self.paginate_queryset(self.queryset)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data).data

        data = self.get_or_set_cache(cache_key, fetch_page, self.POLL_LIST_TIMEOUT)
        return Response(data)

    # -----------------------------
    # Permissions
    # -----------------------------
    def get_permissions(self):
        if self.action in ["list", "results"]:
            return [AllowAny()]
        return [IsAuthenticated()]
