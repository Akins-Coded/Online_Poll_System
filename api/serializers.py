from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "surname", "role"]


class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(
        write_only=True, required=True, error_messages={"required": "Confirm password is required."}
    )
    confirm_email = serializers.EmailField(
        write_only=True, required=True, error_messages={"required": "Confirm email is required."}
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            "required": "Password is required.",
            "min_length": "Password must be at least 8 characters long.",
        },
    )
    role = serializers.ChoiceField(
        choices=User.Roles.choices,
        required=False  # 🔹 role is optional; only admins can set it
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
            "role",
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "surname": {"required": True},
            "email": {"required": True},
        }

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")
        email = attrs.get("email")
        confirm_email = attrs.get("confirm_email")

        if password != confirm_password:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        if email != confirm_email:
            raise serializers.ValidationError({"email": "Emails do not match."})

        return attrs

    def create(self, validated_data):
        # remove confirm fields
        validated_data.pop("confirm_password")
        validated_data.pop("confirm_email")

        password = validated_data.pop("password")

        # 🔹 Enforce role logic
        request = self.context.get("request")
        if not request or not request.user.is_authenticated or request.user.role != User.Roles.ADMIN:
            # Non-admins can only create voter accounts
            validated_data["role"] = User.Roles.VOTER

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
