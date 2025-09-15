from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count
from .models import Poll, Option, Vote
from .serializers import PollSerializer, CreatePollSerializer, AddOptionSerializer, VoteSerializer
from .permissions import IsAdminOrReadOnly
from datetime import datetime
from django.shortcuts import get_object_or_404


class PollViewSet(viewsets.ModelViewSet):
    queryset = Poll.objects.all().select_related("created_by").prefetch_related("options")
    serializer_class = PollSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == "create":
            return CreatePollSerializer
        return PollSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrReadOnly])
    def options(self, request, pk=None):
        """Add option to a poll"""
        poll = self.get_object()
        if datetime.utcnow() >= poll.expires_at:
            return Response({"detail": "Poll expired."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AddOptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(poll=poll)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        """Cast a vote for a poll"""
        poll = self.get_object()
        serializer = VoteSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Vote cast successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def results(self, request, pk=None):
        """Get poll results (optimized with annotate)"""
        poll = self.get_object()
        results = (
            Option.objects.filter(poll=poll)
            .annotate(vote_count=Count("votes"))
            .values("id", "text", "vote_count")
        )

        total_votes = sum(r["vote_count"] for r in results)
        return Response({
            "poll_id": poll.id,
            "title": poll.title,
            "description": poll.description,
            "total_votes": total_votes,
            "results": list(results)
        })
