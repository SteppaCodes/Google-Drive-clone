from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import File, Comment
from .serializers import FileSerializer, CommentSerializer, FileWithCommentsSerialzer
from apps.common.permissions import ISOwner
from apps.common.response import CustomResponse

from django.utils.translation import gettext_lazy as _
from django.http import FileResponse
from django.shortcuts import get_object_or_404


tags = [["Files"], ["Comments"]]

class FileListCreateView(APIView):
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get files",
        description="""
            This endpoint retreives all user's files.
        """,
        tags=tags[0],
        parameters=[
            OpenApiParameter(
                name="query",
                type=str,
                required=False,
                description="Folder name to search for",
            ),
            OpenApiParameter(name="page", type=int, required=False, description="Page number"),
        ],
    )
    def get(self, request):
        user = request.user
        query = request.GET.get("query")
        if query == None:
            query = ""

        files = File.objects.filter(owner=user, name__icontains=query)

        if not files:
            return CustomResponse.success(self, message=_("You do not have any files"))

        serializer = self.serializer_class(files, many=True, context={"request": request})
        return CustomResponse.success( message=_("Files retreived successfully"), data=serializer.data, 
                                      paginate=True, request=request, view=self)



    @extend_schema(
        summary="Upload file",
        description="""
            This endpoint uploads files.
        """,
        tags=tags[0],
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        serializer.save(owner=user)
        return CustomResponse.success(message=_("File uploaded succesfully"), data=serializer.data, status_code=201)

class FileUpdateDestroyView(APIView):
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="update files",
        description="""
            This endpoint updates files.
        """,
        tags=tags[0],
    )
    def put(self, request, id):
        file = File.objects.get(id=id)

        if not file:
            return CustomResponse.error(message=_("File not found"), status_code=404)

        serializer = self.serializer_class(file, data=request.data, context={"request": request})
        serializer.is_valid()
        serializer.save()
        return CustomResponse.success(message=_("File updated successfully"))

    @extend_schema(
        summary="Delete files",
        description="""
            This endpoint deletes files.
        """,
        tags=tags[0],
    )
    def delete(self, request, id):
        file = File.objects.get(id=id)

        if not file:
            return CustomResponse.error(message=_("File not found"), status_code=404)
        
        file.delete()
        return CustomResponse.success(message=_("File deleted successfully"))


class DownloadFileAPIView(APIView):

    @extend_schema(
        summary="Download files",
        description="""
            This endpoint returns file for download.
        """,
        tags=tags[0],
    )
    def get(self, request, file_id):
        try:
            file = File.objects.get(id=file_id)
        except File.DoesNotExist:
            return CustomResponse.error(message=_("File not found"))

        file_path = file.file.path

        # Use FileResponse to handle the file download
        response = FileResponse(open(file_path, "rb"))
        response["Content-Disposition"] = f'attachment; filename="{file.file.name}"'
        return response


class CommentOnFile(APIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Comment on file",
        description="""
            This endpoint add comment to a file.
        """,
        tags=tags[1],
    )
    def post(self, request, id):
        owner = request.user
        file = get_object_or_404(File, id=id)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(file=file, owner=owner)

        return CustomResponse.success(message=_("Comment posted successfully"), data=serializer.data, status_code=201)


class GetFileComments(APIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get comments",
        description="""
            This endpoint retreives all file's comments.
        """,
        tags=tags[1],
    )
    def get(self, request, id):
        file = File.objects.prefetch_related("comments").get(id=id)

        if not file.comments:
            return CustomResponse.success(message=_("File has no comments"))

        serializer = FileWithCommentsSerialzer(file)
        return CustomResponse.success(message=_("Comments retreived successfully"), data=serializer.data, paginate=True, 
                                      request=request, view=self)

    @extend_schema(
        summary="Update comment",
        description="""
            This endpoint updates file's comment.
        """,
        tags=tags[1],
    )
    def put(self, request, id):
        comment = Comment.objects.get(id=id)

        if not comment:
            return CustomResponse.error(message=_("Comment not found"), status_code=404)

        serializer = self.serializer_class(comment, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return CustomResponse.success(message=_("Comment updated successfully"))

    @extend_schema(
        summary="Delete comment",
        description="""
            This endpoint deletes a comment from file.
        """,
        tags=tags[1],
    )
    def delete(self, request, id):
        comment = Comment.objects.get(id=id)
        if request.user == comment.owner or request.user == comment.file.owner:
            comment.delete()
            return Response({"success": "comment deleted succesfully"})
        return Response(
            {"error": "you do not have the permission to delete this comment"}
        )
