from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import StarredItem, SharedItem
from .response import CustomResponse
from .mixins import ItemLookupMixin
from .serializers import StarredItemsSerializer, UserSharedItemsSerializer
from apps.files.serializers import FileSerializer
from apps.folders.serializers import FolderSerializer
from apps.accounts.models import User


tags = ["Common Functionalities"]

class StarItemAPIView(APIView, ItemLookupMixin):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Star an item",
        description="""
            This endpoint stars a file or folder.
        """,
        tags=tags,
    )
    def post(self, request, id):
        item = self.get_item_with_id(request, id)

        if not item:
            return CustomResponse.error(message=_("Item not found"), status_code=404)
        
        serializer = self.serialize(item)

        starred_item, created = StarredItem.objects.get_or_create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(item),
            object_id=id,
        )

        if not created:
            return CustomResponse.error(message=_("Item already starred"))
            
        return CustomResponse.success(message=_("Item starred successfully"), data=serializer.data, status_code=201)


class UnstarItemAPIView(APIView, ItemLookupMixin):
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
        item = self.get_item_with_id(request, id)

        if not item:
            return CustomResponse.error(message=_("Item not found"), status_code=404)

        starred_item = StarredItem.objects.filter(
            user=request.user,
            content_type=ContentType.objects.get_for_model(item),
            object_id=id,
        )

        if not starred_item.exists():
            return CustomResponse.error(message=_("Item not found"), status_code=404)

        starred_item.delete()
        return CustomResponse.success(message=_("Item unstarred successfully"))


class StarredItemsListAPIView(APIView):
    serializer_class = StarredItemsSerializer
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

        if not starred_items:
            return CustomResponse.success(message=_("You do not have any starred item"))

        serializer = self.serializer_class(starred_items, many=True)
        return CustomResponse.success(message=_("Successfully retreive starred items"), data=serializer.data)


class CreateShareLinkAPIView(APIView, ItemLookupMixin):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Share file or folder",
        description="""
            This endpoint creates a link to access file".
        """,
        tags=tags,
    )
    def post(self, request, id):
        item = self.get_item_with_id(request, id)

        if not item:
            return CustomResponse.error(message=_("Item not found"), status_code=404)

        link = self.build_link(request, item)
        data = {
            "link":link
        }

        return CustomResponse.success(message=_("Share link created successfully"), data=data)


class GetSharedItemAPIView(APIView, ItemLookupMixin):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Access file or folder",
        description="""
            This endpoint accesses file/folder through link".
        """,
        tags=tags,
    )
    def get(self, request, type, idb64):
        id = self.decode(idb64)
        item = self.get_item_with_id(request, id)

        if not item:
            return CustomResponse.error(message=_("Item not found"), status_code=404)
        
        serializer = self.serialize(item)

        """
            get or create a shared item object under the hood
            if the item exists, add the user making the request to the list of users with access to the file
        """

        try:
            shared_item, created = SharedItem.objects.get_or_create(
                owner=item.owner,
                content_type=ContentType.objects.get_for_model(item),
                object_id=id,
            )
            # Add the user to the access list if they are not the owner
            if item.owner != request.user:
                shared_item.users.add(request.user)
        except Exception as e:
            return CustomResponse.error(message=_(f"An error occurred: {e}"), status_code=500)

        return CustomResponse.success(message=_("Shared item retrieved successfully"), data=serializer.data)


class UserSharedItemsListCreateAPIView(APIView):
    serializer_class = UserSharedItemsSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get shared files or folders for a user",
        description="""
            This endpoint returns all user's shared files or folders".
        """,
        tags=tags,
    )
    def get(self, request):

        user = User.objects.get(id=request.user.id)

        shared_items = user.shared_items.all() # Items where the user is the owner
        collab_items = user.collab_items.all() # Items where the user is a part of the users that hav access to a shared item

        shared_items_serializer = self.serializer_class(shared_items, many=True)
        collab_items_serializer = self.serializer_class(collab_items, many=True) 

        data = {
            "shared_items": shared_items_serializer.data,
            "collab_items": collab_items_serializer.data,
        }

        return CustomResponse.success(message=_("Shared items retreived successfully"), data=data)


class SharedItemDetailAPIView(APIView):
    serializer_class = UserSharedItemsSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Shared item detail",
        description="""
            This endpoint returns the details of a shared item".
        """,
        tags=tags,
    )
    def get(self, request, id):
        try:
            shared_item = SharedItem.objects.get(id=id)
            serializer = self.serializer_class(
                shared_item, context={"request": request}
            )
            return CustomResponse.success(message=_("Item retrieved successfully"), data=serializer.data)
        except SharedItem.DoesNotExist:
            return CustomResponse.error(message=_("Item not found"), status_code=404)


class SearchDriveAPIView(APIView, ItemLookupMixin):
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

        obj = self.search_item(request, query)
        files, folders = obj[0], obj[1]

        file_serializer = FileSerializer(files, many=True)
        folder_serializer = FolderSerializer(folders, many=True)
        data = {
            "files": file_serializer.data,
            "folders":folder_serializer.data
        }

        return CustomResponse.success(message=_("Search successful"), data=data)


