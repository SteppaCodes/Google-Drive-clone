from django.utils.translation import gettext_lazy as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Folder
from .serializers import FolderSerializer


class FolderListCreateAPIView(APIView):
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        folders =  Folder.objects.filter(owner=user)
        if folders:
            serializer = self.serializer_class(folders, many=True)
            return Response({"data":serializer.data})
        else:
            return Response(_("You do not have any folders"))
    

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        serializer.save(owner=user)

        return Response({"success":"Folder created", "data":serializer.data})