from rest_framework import serializers
from .models import Poll, Option, Vote
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "text"]


class PollSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Poll
        fields = ["id", "title", "description", "created_by", "created_at", "expires_at", "options"]


class CreatePollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ["title", "description", "expires_at"]

    def create(self, validated_data):
        return Poll.objects.create(created_by=self.context["request"].user, **validated_data)


class AddOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["text"]


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
        if datetime.utcnow() >= poll.expires_at:
            raise serializers.ValidationError({"poll": "Poll has expired."})

        if Vote.objects.filter(user=user, poll=poll).exists():
            raise serializers.ValidationError({"poll": "User has already voted on this poll."})

        attrs["poll"] = poll
        attrs["option"] = option
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        return Vote.objects.create(user=user, **validated_data)
