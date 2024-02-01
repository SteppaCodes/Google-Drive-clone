from django.utils.translation import gettext_lazy as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Folder
from .serializers import FolderSerializer, FolderWIthFilesSerializer

#TODO ddd response statuses

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


class FolderDetailAPIView(APIView):
    serializer_class =  FolderSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        folder = Folder.objects.prefetch_related('files').get(id=id)
        serializer = FolderWIthFilesSerializer(folder)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, id):
        folder = Folder.objects.get(id=id)
        serializer = self.serializer_class(folder, data=request.data)
        serializer.is_valid(raise_exceptions=True)
        serializer.save()

        return Response({"success":"Folder updateed successfully", "data":serializer.data})
    
    def delete(self, request, id):
        folder = Folder.objects.get(id=id)
        if folder.owner == request.user:
            folder.delete()
            return Response({"success":"folder deleted successfully"}) 