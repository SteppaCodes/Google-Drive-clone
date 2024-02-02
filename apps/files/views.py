from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import File
from .serializers import FileSerializer


from django.utils.translation import gettext_lazy as _
from django.http import FileResponse


class FileListCreateView(APIView):
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        files = File.objects.filter(owner=user)
       
        if files:
            serializer = self.serializer_class(files, many=True, context={"request":request})
            return Response({"data":serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response(_("You do not have any files"))
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request":request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        serializer.save(owner=user)
        return Response({"data":serializer.data}, status=status.HTTP_201_CREATED)
        

class FileUpdateDestroyView(APIView):
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]
    
    def put(self, request, id):
        file = File.objects.get(id=id)
        serializer = self.serializer_class(file, data=request.data, context={"request":request})
        serializer.is_valid()
        serializer.save()
        return Response({"Success":"file update succesflly",
                        "data":serializer.data})

    def delete(self, request, id):
        file = File.objects.get(id=id)
        file.delete()

        return Response({"success":"file deleted succesfully"})


class DownloadFileAPIView(APIView):
    
    def get(self, request, file_id):
        try:
            file = File.objects.get(id=file_id)
        except File.DoesNotExist:
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
        
        file_path = file.file.path

        # Use FileResponse to handle the file download
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{file.file.name}"'
        return response


