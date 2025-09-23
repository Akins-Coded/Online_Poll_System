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
    """Read-only option serializer with vote count (safe fallback)."""
    votes_count = serializers.SerializerMethodField()

    class Meta:
        model = Option
        fields = ["id", "text", "votes_count"]

    def get_votes_count(self, obj):
        # Use annotated value if available, else fallback to .count()
        return getattr(obj, "votes_count", obj.votes.count())


class OptionTextSerializer(serializers.Serializer):
    """Used for poll creation: accepts {"text": "Option A"}."""
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
    """Read serializer: includes options + creator info + total votes."""
    options = OptionSerializer(many=True, read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    total_votes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Poll
        fields = [
            "id",
            "title",
            "description",
            "created_by",
            "created_at",
            "expires_at",
            "total_votes",
            "options",
        ]


class CreatePollSerializer(serializers.ModelSerializer):
    """
    Creates a poll and multiple options in one request.
    Options can be:
        ["Rice", "Beans"]
        or
        [{"text": "Rice"}, {"text": "Beans"}]
    """
    options = serializers.ListField(child=serializers.JSONField(), write_only=True, required=True)

    class Meta:
        model = Poll
        fields = ["title", "description", "expires_at", "options"]

    def to_internal_value(self, data):
        options = data.get("options", [])
        normalized = []
        for item in options:
            if isinstance(item, str):
                normalized.append({"text": item})
            elif isinstance(item, dict) and "text" in item:
                normalized.append(item)
            else:
                raise serializers.ValidationError(
                    {"options": "Each option must be a string or an object with a 'text' field."}
                )
        data["options"] = normalized
        return super().to_internal_value(data)

    def create(self, validated_data):
        options_data = validated_data.pop("options", [])
        poll = Poll.objects.create(created_by=self.context["request"].user, **validated_data)
        Option.objects.bulk_create([Option(poll=poll, text=o["text"]) for o in options_data])
        return poll


# -----------------------------
# Vote Serializer
# -----------------------------
class VoteSerializer(serializers.ModelSerializer):
    """
    Accepts {"option_id": <id>} to cast a vote.
    Validates option existence & poll expiry.
    Handles race conditions via IntegrityError.
    Returns option details + timestamp for clients.
    """
    option_id = serializers.IntegerField(write_only=True)
    option = OptionSerializer(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Vote
        fields = ["option_id", "option", "timestamp"]

    def validate(self, attrs):
        option_id = attrs.get("option_id")

        try:
            option = Option.objects.select_related("poll").get(pk=option_id)
        except Option.DoesNotExist:
            raise serializers.ValidationError({"option_id": "Option not found."})

        if option.poll.expires_at and timezone.now() >= option.poll.expires_at:
            raise serializers.ValidationError({"poll": "Poll has expired."})

        attrs["option"] = option
        attrs["poll"] = option.poll
        return attrs

        # Expiration check
        if poll.expires_at and timezone.now() >= poll.expires_at:
            raise serializers.ValidationError({"poll": "Poll has expired."})

        attrs["option"] = option
        attrs["poll"] = poll
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        try:
            return Vote.objects.create(user=user, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"poll": "User has already voted in this poll."})

    def update(self, instance, validated_data):
        raise serializers.ValidationError("Votes cannot be updated, only deleted/re-cast.")