from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
import uuid

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Folder
from .serializers import FolderSerializer
from apps.files.serializers import FileSerializer


tags = ["Folders"]


class FolderListCreateAPIView(APIView, PageNumberPagination):
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticated]
    page_size = 5

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
        if folders:
            paginated_qs = self.paginate_queryset(folders, request, view=self)
            serializer = self.serializer_class(
                paginated_qs, many=True, context={"request": request}
            )
            return self.get_paginated_response({"data": serializer.data})
        else:
            return Response(_("You do not have any folders"))

    @extend_schema(
        summary="Create folder",
        description="""
            This endpoint creates a new folder.
        """,
        tags=tags,
    )
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)

        return Response({"success": "Folder created", "data": serializer.data})


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
        try:
            query = request.GET.get("query")

            if query == None:
                query = ""

            folder = Folder.objects.prefetch_related("files", "subfolders").get(id=id)
            serializer = self.serializer_class(folder)

            # Get the files and filter them based on the query
            files = folder.files.filter(name__icontains=query)
            flle_serializer = FileSerializer(files, many=True)

            sub_folders = folder.subfolders.filter(name__icontains=query)
            sub_folder_serializer = FolderSerializer(sub_folders, many=True)

            return Response(
                {
                    "data": {
                        "folder": serializer.data,
                        "files": flle_serializer.data,
                        "subfolders": sub_folder_serializer.data,
                    }
                },
                status=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            return Response(_("This folder does not exist"))

    @extend_schema(
        summary="Update folders",
        description="""
            This endpoint updates folder information.
        """,
        tags=tags,
    )
    def put(self, request, id):
        folder = Folder.objects.get(id=id)
        serializer = self.serializer_class(
            folder, data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                {"success": "Folder updated successfully", "data": serializer.data}
            )
        return Response(serializer.errors)

    @extend_schema(
        summary="Delete folders",
        description="""
            This endpoint deletes a folder.
        """,
        tags=tags,
    )
    def delete(self, request, id):
        folder = Folder.objects.get(id=id)
        if folder.owner == request.user:
            folder.delete()
            return Response({"success": "folder deleted successfully"})
