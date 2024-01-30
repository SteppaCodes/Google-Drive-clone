from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .serializers import RegisterUserSerializer, LoginUserSerializer


class RegisteruserView(APIView):
    serializer_class = RegisterUserSerializer

    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success":"user registered succesfully", "data":serializer.data}, 
                                                          status=status.HTTP_201_CREATED)

class LoginUserView(APIView):
    serializer_class = LoginUserSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response({"success":"Login successful", 'data':serializer.data}, 
                                                    status=status.HTTP_200_OK)
