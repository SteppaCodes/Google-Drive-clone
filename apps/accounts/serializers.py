from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from .models import User

class RegisterUserSerializer(serializers.ModelSerializer):
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
        
    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password!= password2:
            raise serializers.ValidationError(_("passwords do not match"))
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name= validated_data['first_name'],
            last_name = validated_data['last_name'],
            password = validated_data['password']
        )
        return user

class LoginUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=30, min_length=8, write_only=True)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
                'email',
                'password',
                'full_name',
                'access_token',
                'refresh_token',
                ]

    def validate(self, attrs):
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

