#django imports
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator

#Third party imports
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

#Local imports
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar",
            
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=30, min_length=8, write_only=True)
    password2 = serializers.CharField(max_length=30, min_length=8, write_only=True)

    class Meta:
        model = User
        fields = [
                'first_name',
                'last_name',
                'email',
                'password',
                'password2',
                "terms_agreement"
            ]

        
    def validate(self, attrs: dict) -> dict:
        password = attrs.get('password')
        password2 = attrs.get('password2')
        terms_agreement = attrs.get("terms_agreement")
        if password!= password2:
            raise serializers.ValidationError(_("passwords do not match"))
        
        if not terms_agreement:
            raise serializers.ValidationError(_("you must agree to the terms of service"))
        return attrs
    
    def create(self, validated_data: dict) -> User:
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name= validated_data['first_name'],
            last_name = validated_data['last_name'],
            password = validated_data['password'],
            terms_agreement=validated_data['terms_agreement']
        )
        return user


class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOtpSerializer(ResendOtpSerializer):
    otp = serializers.IntegerField()


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField(read_only=True)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
                'id',
                'email',
                'password',
                'full_name',
                'access_token',
                'refresh_token',
                ]

        read_only_fields = ["id"]

    def validate(self, attrs: dict) -> dict:
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(email=email, password=password)

        if not user:
            raise AuthenticationFailed(_("Authentication failed!. Credentials is invalid"))
        token = user.tokens()
        return {
            'email':user.email,
            'full_name':user.full_name,
            'access_token':str(token.get("access")),
            'refresh_token':str(token.get("refresh"))
        }


class ResetPasswordSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    class Meta:
        model = User
        fields = [
                'email',
                ]


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=30, min_length=8, write_only=True)
    confirm_password = serializers.CharField(max_length=30, min_length=8, write_only=True)
    token = serializers.CharField(write_only=True)
    uidb64 = serializers.CharField(write_only=True)
    
    class Meta:
        fields = [
            'password',
            'confirm_password',
            'token',
            'uidb64'
        ]

    def validate(self, attrs: dict) -> dict:
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        token = attrs.get('token')
        uidb64 = attrs.get('uidb64')

        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)

            if PasswordResetTokenGenerator().check_token(user, token):
                if password == confirm_password:
                    user.set_password(password)
                    user.save()
                    return attrs
                else:
                    raise AuthenticationFailed('passwords do not match')
            raise AuthenticationFailed('Link is invalid or expired')
        except Exception as e:
            raise AuthenticationFailed('Link is invalid or expired')
        

class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    default_error_messages = {
        "bad token":("token is invalid or expired")
    }

    def validate(self, attrs: dict) -> dict:
        self.token =  attrs.get("refresh_token")
        return attrs

    def save(self, **Kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail("Bad token")