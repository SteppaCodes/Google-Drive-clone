from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import File
from .serializers import FileSerializer


from django.utils.translation import gettext_lazy as _

class FileListCreateView(APIView):
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        files = File.objects.filter(owner=user)
       
        if files:
            serializer = self.serializer_class(files, many=True)
            return Response({"data":serializer.data})
        else:
            return Response(_("You do not have any files"))
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        serializer.save(owner=user)
        return Response({"data":serializer.data}, status=status.HTTP_201_CREATED)
        