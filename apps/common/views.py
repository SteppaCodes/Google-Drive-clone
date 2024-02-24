from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.db.models import Q

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import StarredItem, SharedItem
from .serializers import StarredItemsSerielizer, UserSharedItemsSerializer
from apps.files.models import File
from apps.folders.models import Folder
from apps.files.serializers import FileSerializer
from apps.folders.serializers import FolderSerializer
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer

tags = ["Common Functionalities"]


class Finder:
    @staticmethod
    def get_item_with_id(request, id):
        try:
            item = File.objects.get(id=id)
            serializer = FileSerializer(item, context={"request": request})
            return item, serializer
        except ObjectDoesNotExist:
            try:
                item = Folder.objects.get(id=id)
                serializer = FolderSerializer(item, context={"request": request})
                return item, serializer
            except ObjectDoesNotExist:
                return None, None

    @staticmethod
    def Search_item(request, query):

        try:
            files = File.objects.filter(name__icontains=query, owner=request.user)
            folders = Folder.objects.filter(name__icontains=query, owner=request.user)
            return files, folders
        except ObjectDoesNotExist:
            return None, None


class StarItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Star an item",
        description="""
            This endpoint stars a file or folder.
        """,
        tags=tags,
    )
    def post(self, request, id):
        item, serializer = Finder.get_item_with_id(request, id)

        if item is None:
            return Response(
                {
                    "error": "Item not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        starred_item, created = StarredItem.objects.get_or_create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(item),
            object_id=id,
        )
        if created:
            return Response(
                {"success": "Item starred", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"detail": "Item is already starred", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class UnstarItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Unstar an item",
        description="""
            This endpoint unstars a file or folder.
        """,
        tags=tags,
        parameters=[
            OpenApiParameter(
                name="id",
                description="Retrieve a folder using its id",
                required=True,
            )
        ],
    )
    def delete(self, request, id):
        item, serializer = Finder.get_item_with_id(request, id)

        if item is None:
            return Response(
                {
                    "error": "Not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        starred_item = StarredItem.objects.filter(
            user=request.user,
            content_type=ContentType.objects.get_for_model(item),
            object_id=id,
        )

        if starred_item.exists():
            starred_item.delete()
            return Response({"success": "item unstarred", "data": serializer.data})

        else:
            return Response({"error": "Item not starred"})


class StarredItemsListAPIView(APIView):
    serializer_class = StarredItemsSerielizer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retreive starred files and folders",
        description="""
            This endpoint retreives all starred folders and files".
        """,
        tags=tags,
    )
    def get(self, request):
        starred_items = StarredItem.objects.filter(user=request.user)
        if starred_items:
            serializer = self.serializer_class(starred_items, many=True)
            return Response({"data": serializer.data})
        else:
            return Response(_("You do not have any starred item"))


class CreateShareLinkAPIview(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Share file or folder",
        description="""
            This endpoint creates a link to access file".
        """,
        tags=tags,
    )
    def post(self, request, id):
        item, serializer = Finder.get_item_with_id(request, id)

        if item is None:
            return Response(
                {
                    "error": "Item not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Build the link
        site = get_current_site(request).domain
        id = item.id
        item_type = item._meta.model.__name__
        type = ""

        if item_type == "File":
            type = "files"
        else:
            type = "folders"

        url = reverse("get-shared-item", args=[type, id])
        link = f"{request.scheme}://{site}{url}"

        return Response({"link": link})


class GetSharedItemAPIview(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Access file or folder",
        description="""
            This endpoint accesses file/folder through link".
        """,
        tags=tags,
    )
    def get(self, request, type, id):
        item, serializer = Finder.get_item_with_id(request, id)

        if item is None:
            return Response(
                {
                    "error": "Item not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        """
            get or create a shared item object under the hood
            if the item exists, add the user making the request to-
            -the list of users with access to the file
        """

        try:
            shared_item, created = SharedItem.objects.get_or_create(
                owner=request.user,
                content_type=ContentType.objects.get_for_model(item),
                object_id=id,
            )
            if not created:
                users = shared_item.users
                # exclude the file owner from the list
                if shared_item.owner != request.user:
                    users.add(request.user)
        except Exception as e:
            return Response({"error": e})

        return Response({"data": serializer.data})


class UserSharedItemsListCreateAPIview(APIView):
    serializer_class = UserSharedItemsSerializer

    @extend_schema(
        summary="Get shared files or folders for a user",
        description="""
            This endpoint returns all user's shared files or folders".
        """,
        tags=tags,
    )
    def get(self, request):

        user = User.objects.get(id=request.user.id)

        shared_items = user.shared_items.all()
        collab_items = user.collab_items.all()

        shared_items_serializer = self.serializer_class(shared_items, many=True)
        collab_items_serializer = self.serializer_class(collab_items, many=True)

        data = {
            "shared_items": shared_items_serializer.data,
            "collab_items": collab_items_serializer.data,
        }

        return Response({"data": data})


class SharedItemDetailAPIView(APIView):
    serializer_class = UserSharedItemsSerializer

    def get(self, request, id):
        try:
            shared_item = SharedItem.objects.get(id=id)
            serializer = self.serializer_class(
                shared_item, context={"request": request}
            )
            return Response({"data": serializer.data})
        except ObjectDoesNotExist:
            return Response({"error": "item does not exist"})


class SearchDriveAPIview(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Search drive",
        description="""
            This endpoint searches all files and folders in drive".
        """,
        tags=tags,
    )
    def get(self, request):
        query = request.GET.get("query")

        if query == None:
            query = ""

        obj = Finder.Search_item(request, query)
        files, folders = obj[0], obj[1]

        file_serializer = FileSerializer(files, many=True)
        folder_serializer = FolderSerializer(folders, many=True)

        return Response(
            {"data": {"files": file_serializer.data, "folders": folder_serializer.data}}
        )
