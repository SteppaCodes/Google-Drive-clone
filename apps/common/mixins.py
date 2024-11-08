from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site

from apps.files.models import File
from apps.files.serializers import FileSerializer
from apps.folders.models import Folder
from apps.folders.serializers import FolderSerializer


class AgentMixin:
    @staticmethod
    def get_item_with_id(request, id=None, idb64=None):
        if idb64:
            id = force_str(urlsafe_base64_decode(idb64))
        try:
            item = File.objects.get(id=id)
            return item
        except File.DoesNotExist:
            try:
                item = Folder.objects.get(id=id)
                return item
            except Folder.DoesNotExist:
                return None

    @staticmethod
    def search_item(request, query):

        try:
            files = File.objects.filter(name__icontains=query, owner=request.user)
            folders = Folder.objects.filter(name__icontains=query, owner=request.user)
            return files, folders
        except ObjectDoesNotExist:
            return None, None

    @staticmethod
    def serialize(self, item, many=False):
        if isinstance(item, File):
            item = FileSerializer(item, many)
        
        elif isinstance(item, Folder):
            item = FolderSerializer(item, many)
        
        else:
            raise ValueError(_("Invalid item"))
        
        return item
    
    @staticmethod
    def build_link(self, request, item):
        site = get_current_site(request).domain
        idb64 = self.encode(item.id)
        item_type = item._meta.model.__name__ # Get the model name
        type = ""

        # Dynamically set url type eg ..get-shared-itmes/files or get-shared-items/folders
        if item_type == "File":
            type = "files"
        else:
            type = "folders"

        url = reverse("get-shared-item", args=[type, idb64])
        link = f"{request.scheme}://{site}{url}"

        return link
    
    @staticmethod
    def encode(self, item_id):
        idb64 = urlsafe_base64_encode(force_bytes(item_id))
        return idb64
    
    @staticmethod
    def decode(self, idb64):
        id = force_str(urlsafe_base64_decode(idb64))
        return id
    


