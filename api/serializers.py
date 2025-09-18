from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for basic user details."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "surname", "role"]


class AdminCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating admins only."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            "required": "Password is required.",
            "min_length": "Password must be at least 8 characters long.",
        },
    )

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "surname"]

    def create(self, validated_data):

        validated_data["role"] = User.Roles.ADMIN
        validated_data["is_staff"] = True
        validated_data["is_superuser"] = True

        user = User.objects.create_user(**validated_data)
        return user


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user self-registration (non-admins always become voters)."""

    confirm_password = serializers.CharField(write_only=True, required=True)
    confirm_email = serializers.EmailField(write_only=True, required=True)
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            "required": "Password is required.",
            "min_length": "Password must be at least 8 characters long.",
        },
    )

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "surname",
            "email",
            "confirm_email",
            "password",
            "confirm_password",
           
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "surname": {"required": True},
            "email": {"required": True},
        }

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError({"password": "Passwords do not match."})

        if attrs.get("email") != attrs.get("confirm_email"):
            raise serializers.ValidationError({"email": "Emails do not match."})

        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        validated_data.pop("confirm_email", None)
        password = validated_data.pop("password")

        request = self.context.get("request")
        if not request or not request.user.is_authenticated or request.user.role != User.Roles.ADMIN:
            validated_data["role"] = User.Roles.VOTER  # enforce voter role

        user = User.objects.create_user(password=password, **validated_data)
        return user
