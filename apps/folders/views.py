from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Folder
from .serializers import FolderSerializer, FolderWIthFilesSerializer

#TODO add response statuses

class FolderListCreateAPIView(APIView):
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        folders =  Folder.objects.filter(owner=user)
        if folders:
            serializer = self.serializer_class(folders, many=True, context={"request":request})
            return Response({"data":serializer.data})
        else:
            return Response(_("You do not have any folders"))
    

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request":request})
        serializer.is_valid(raise_exceptions=True)

        user = request.user
        serializer.save(owner=user)

        return Response({"success":"Folder created", "data":serializer.data})


class FolderDetailAPIView(APIView):
    serializer_class =  FolderSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            folder = Folder.objects.prefetch_related('files', 'subfolders').get(id=id)
            serializer = FolderWIthFilesSerializer(folder)
            return Response({"data":serializer.data}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(_("This folder does not exist"))
        

    def put(self, request, id):
        folder = Folder.objects.get(id=id)
        serializer = self.serializer_class(folder, data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"success":"Folder updated successfully", "data":serializer.data})

        return Response(serializer.errors)
    
    def delete(self, request, id):
        folder = Folder.objects.get(id=id)
        if folder.owner == request.user:
            folder.delete()
            return Response({"success":"folder deleted successfully"}) 


