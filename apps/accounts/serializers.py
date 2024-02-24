from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=30, min_length=8, write_only=True)
    password2 = serializers.CharField(max_length=30, min_length=8, write_only=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "password2",
            "terms_agreement",
        ]

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        password2 = attrs.get("password2")
        terms_agreement = attrs.get("terms_agreement")

        user = User.objects.filter(email=email).first()
        if user:
            raise serializers.ValidationError(
                {"error": "User with this Email already exists"}
            )

        if password != password2:
            raise serializers.ValidationError(_("passwords do not match"))

        if not terms_agreement:
            raise serializers.ValidationError(
                {"error": "You must agree to terms and conditions"}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user


class LoginUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=30, min_length=8, write_only=True)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "full_name",
            "access_token",
            "refresh_token",
        ]

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(email=email, password=password)

        if not user:
            raise AuthenticationFailed(
                _("Authentication failed!. Credentials is invalid")
            )
        token = user.tokens()
        return {
            "email": user.email,
            "full_name": user.full_name,
            "access_token": str(token.get("access")),
            "refresh_token": str(token.get("refresh")),
        }


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    default_error_messages = {"Bad token": ("token is expired or invalid")}

    def validate(self, attrs):
        self.token = attrs.get("refresh_token")
        return attrs

    def save(self, **Kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail("Bad token")
