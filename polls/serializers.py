from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Poll, Option, Vote

User = get_user_model()


# -----------------------------
# Option Serializer
# -----------------------------
class OptionSerializer(serializers.ModelSerializer):
    votes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Option
        fields = ["id", "text", "votes_count"]

class AddOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "text"]

    def create(self, validated_data):
        return Option.objects.create(**validated_data)


# -----------------------------
# Poll Serializers
# -----------------------------
class PollSerializer(serializers.ModelSerializer):
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
    # Allow creating poll + options inline
    options = serializers.ListField(
        child=serializers.CharField(max_length=255),
        write_only=True,
        required=True
    )

    class Meta:
        model = Poll
        fields = ["title", "description", "expires_at", "options"]

    def create(self, validated_data):
        options_data = validated_data.pop("options", [])
        poll = Poll.objects.create(
            created_by=self.context["request"].user, **validated_data
        )
        Option.objects.bulk_create([
            Option(poll=poll, text=opt["text"]) for opt in options_data
        ])
        return poll


# -----------------------------
# Vote Serializer
# -----------------------------
class VoteSerializer(serializers.ModelSerializer):
    option_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Vote
        fields = ["option_id"]

    def validate(self, attrs):
        user = self.context["request"].user
        option_id = attrs["option_id"]

        try:
            option = Option.objects.select_related("poll").get(pk=option_id)
        except Option.DoesNotExist:
            raise serializers.ValidationError({"option_id": "Option not found."})

        poll = option.poll

        # Check if poll is expired
        if timezone.now() >= poll.expires_at:
            raise serializers.ValidationError({"poll": "Poll has expired."})

        # Prevent duplicate votes
        if Vote.objects.filter(user=user, poll=poll).exists():
            raise serializers.ValidationError({"poll": "User has already voted in this poll."})

        attrs["poll"] = poll
        attrs["option"] = option
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        return Vote.objects.create(user=user, **validated_data)
