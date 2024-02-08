from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import StarredItem
from .serializers import StarredItemsSerielizer
from apps.files.models import File
from apps.folders.models import Folder
from apps.files.serializers import FileSerializer
from apps.folders.serializers import FolderSerializer


def get_item(self, id, request):
    try:
        item = File.objects.get(id=id)
        serializer = FileSerializer(item, context={'request':request})
        return item, serializer
    except ObjectDoesNotExist:
        try:
            item = Folder.objects.get(id=id)
            serializer = FolderSerializer(item, context={'request':request})
            return item, serializer
        except ObjectDoesNotExist:
            return Response({"error":"item does not exist"})


class StarItemAPIView(APIView):
    def post(self, request, id):
        #Get the item to be starred, if its a folder or file
        obj = get_item(self, id, request)
        #get the returnd item and serialzer rfo the get_item function
        item , serializer = obj[0],obj[1]

        starred_item, created = StarredItem.objects.get_or_create(user=request.user,  
                                                                  content_type=ContentType.objects.get_for_model(item), object_id=id)
        if created:
            return Response({"success":"Item starred","data":serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"detail": "Item is already starred", "data": serializer.data}, status=status.HTTP_200_OK)


class UnstarItemAPIView(APIView):
    def delete(self, request, id):
       #Get the item to be starred, if its a folder or file
        obj = get_item(self,id, request)
        item , serializer = obj[0],obj[1]

        starred_item = StarredItem.objects.filter(user=request.user, 
                                                  content_type=ContentType.objects.get_for_model(item), object_id=id)
        
        if starred_item.exists():
            starred_item.delete()
            return Response({"success":"item unstarred", 'data':serializer.data})
        
        else:
            return Response({"error":"you cannot unstar an item that has not been starred"})


class StarredItemsListAPIView(APIView):
    serializer_class = StarredItemsSerielizer
    permission_classes = [IsAuthenticated]
    def get(self, request):
        starred_items = StarredItem.objects.filter(user=request.user)
        if starred_items:
            serializer = self.serializer_class(starred_items, many=True)
            return Response({"data":serializer.data})
        else:
            return Response(_("You do not have any starred item"))


class CreateShareLink(APIView):
    def post(self, request, id):
        obj = get_item(self, id, request)
        item = obj[0]

        #Build the link
        site = get_current_site(request).domain
        id = item.id
        item_type = item._meta.model.__name__
        type  = ''

        if item_type == 'File':
            type = 'files'
        else:
            type = 'folders'

        url = reverse('get-shared-item', args=[type, id])
        link = f"{request.scheme}://{site}{url}"

        return Response({"link":link})


class GetSharedItem(APIView):
    def get(self, request, id, type):
        obj = get_item(self, id, request)
        serializer = obj[1]

        return Response({"data":serializer.data})

