from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import IntegrityError

from .models import Poll, Option, Vote

User = get_user_model()


# -----------------------------
# Option Serializers
# -----------------------------
class OptionSerializer(serializers.ModelSerializer):
    """Read-only option serializer with vote count."""
    votes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Option
        fields = ["id", "text", "votes_count"]


class OptionTextSerializer(serializers.Serializer):
    """Used for poll creation: accepts objects like {"text": "Option A"}."""
    text = serializers.CharField(max_length=255)


class AddOptionSerializer(serializers.ModelSerializer):
    """
    Adds a single option to a poll.
    The view must call serializer.save(poll=poll).
    """
    class Meta:
        model = Option
        fields = ["id", "text"]

    def create(self, validated_data):
        poll = validated_data.pop("poll", None)
        if poll is None:
            raise serializers.ValidationError({"poll": "Poll must be provided."})
        return Option.objects.create(poll=poll, **validated_data)


# -----------------------------
# Poll Serializers
# -----------------------------
class PollSerializer(serializers.ModelSerializer):
    """Read serializer: includes options + creator info."""
    options = OptionSerializer(many=True, read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Poll
        fields = [
            "id",
            "title",
            "description",
            "created_by",
            "created_at",
            "expires_at",
            "options",
        ]


class CreatePollSerializer(serializers.ModelSerializer):
    """
    Creates a poll and multiple options in one request.
    Input format:
    {
        "title": "Best language?",
        "description": "Vote your favorite",
        "expires_at": "2025-12-31T23:59:59Z",
        "options": [{"text": "Python"}, {"text": "JavaScript"}]
    }
    """
    options = OptionTextSerializer(many=True, write_only=True, required=True)

    class Meta:
        model = Poll
        fields = ["title", "description", "expires_at", "options"]

    def create(self, validated_data):
        options_data = validated_data.pop("options", [])
        request = self.context.get("request", None)
        created_by = getattr(request, "user", None)

        # Create poll
        poll = Poll.objects.create(created_by=created_by, **validated_data)

        # Bulk create options
        Option.objects.bulk_create([Option(poll=poll, text=o["text"]) for o in options_data])

        return poll


# -----------------------------
# Vote Serializer
# -----------------------------
class VoteSerializer(serializers.ModelSerializer):
    """
    Accepts {"option_id": <id>} to cast a vote.
    Validates option existence, poll expiry, and duplicate votes.
    Handles race conditions via IntegrityError.
    """
    option_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Vote
        fields = ["option_id"]

    def validate(self, attrs):
        user = self.context["request"].user
        option_id = attrs.get("option_id")

        try:
            option = Option.objects.select_related("poll").get(pk=option_id)
        except Option.DoesNotExist:
            raise serializers.ValidationError({"option_id": "Option not found."})

        poll = option.poll

        # Expiration check
        if poll.expires_at is not None and timezone.now() >= poll.expires_at:
            raise serializers.ValidationError({"poll": "Poll has expired."})

        # Duplicate check
        if Vote.objects.filter(user=user, poll=poll).exists():
            raise serializers.ValidationError({"poll": "User has already voted in this poll."})

        attrs["option"] = option
        attrs["poll"] = poll
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        option = validated_data.pop("option")
        poll = validated_data.pop("poll")

        try:
            vote = Vote.objects.create(user=user, poll=poll, option=option)
        except IntegrityError:
            raise serializers.ValidationError({"poll": "User has already voted in this poll."})

        return vote
