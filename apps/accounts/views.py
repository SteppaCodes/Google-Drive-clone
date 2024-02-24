from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import RegisterUserSerializer, LoginUserSerializer, LogoutSerializer

tags = ["Auth"]


class RegisteruserView(APIView):
    serializer_class = RegisterUserSerializer

    @extend_schema(
        summary="Register User",
        description="""
            This endpoint registers a new user.
        """,
        tags=tags,
    )
    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"success": "user registered succesfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


class LoginUserView(APIView):
    serializer_class = LoginUserSerializer

    @extend_schema(
        summary="Login User",
        description="""
            This endpoint authenticates a user.
        """,
        tags=tags,
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {"success": "Login successful", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class LogoutUserAPIView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Logout User",
        description="""
            This endpoint logs out a user.
        """,
        tags=tags,
        examples=[
            OpenApiExample(
                name="Logout user example",
            )
        ]
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "Logout Successful"})
