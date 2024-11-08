from django.utils.translation import gettext_lazy as _

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Folder
from .serializers import FolderSerializer
from apps.files.serializers import FileSerializer
from apps.common.response import CustomResponse


tags = ["Folders"]


class FolderListCreateAPIView(APIView):
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve folders",
        description="""
            This endpoint retrieves all folders a user has access to.
        """,
        tags=tags,
        parameters=[
            OpenApiParameter(
                name="query",
                type=str,
                required=False,
                description="Folder name to search for"
            ),
            OpenApiParameter(
                name="page",
                type=int,
                required=False,
                description="Page number"
            )
        ]
    )
    def get(self, request):
        user = request.user

        query = request.GET.get("query")
        if query == None:
            query = ""

        folders = Folder.objects.filter(owner=user, name__icontains=query)

        if not folders:
            return CustomResponse.success(message=_("You do not have any folders"))
        
        serializer = self.serializer_class(folders, many=True, context={"request": request})
        return CustomResponse.success(message=_("Folders retreived successfully"), data=serializer.data, paginate=True, request=request, view=None)


    @extend_schema(
        summary="Create folder",
        description="""
            This endpoint creates a new folder.
        """,
        tags=tags,
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)

        return CustomResponse.success(message=_("Folder created successfully", data=serializer.data, status_code=201))


class FolderDetailAPIView(APIView):
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve specific folder",
        description="""
            This endpoint retrieves contents of a folder (files and folders).
        """,
        tags=tags,
        parameters=[
            OpenApiParameter(
                name="query",
                type=str,
                required=False,
                description="Folder or file name to search for"
            )
        ]
    )
    def get(self, request, id):
        query= request.query_params if not None else ""

        folder = Folder.objects.prefetch_related("files", "subfolders").get(id=id)
        if not folder:
            return CustomResponse.error(message=_("Folder not found"), status_code=404)

        serializer = self.serializer_class(folder)

        # Get the files and filter them based on the query
        files = folder.files.filter(name__icontains=query)
        flle_serializer = FileSerializer(files, many=True)

        sub_folders = folder.subfolders.filter(name__icontains=query)
        sub_folder_serializer = FolderSerializer(sub_folders, many=True)

        data = {
            "folder": serializer.data,
            "files": flle_serializer,
            "folders": sub_folder_serializer.data
        }
        
        return CustomResponse.success(message=_("Folder details retreived successfully"), data=data)


    @extend_schema(
        summary="Update folders",
        description="""
            This endpoint updates folder information.
        """,
        tags=tags,
    )
    def put(self, request, id):
        folder = Folder.objects.get(id=id)

        if not folder:
            return CustomResponse.error(message=_("Folder not found"), status_code=404)
        
        serializer = self.serializer_class(folder, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return CustomResponse.success(message=_("Folder detail updated successfully"), data=serializer.data)

    @extend_schema(
        summary="Delete folders",
        description="""
            This endpoint deletes a folder.
        """,
        tags=tags,
    )
    def delete(self, request, id):
        folder = Folder.objects.get(id=id)

        if not folder:
            return CustomResponse.error(message=_("Folder not found"), status_code=404)
        
        if folder.owner != request.user:
            return CustomResponse.error(message=_("You cannot delete this folder"))
        
        folder.delete()
        return CustomResponse.success(message=_("Folder deleted successfully"))