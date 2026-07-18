from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from apps.files.models import File
from apps.files.serializers import FileSerializer
from apps.folders.models import Folder
from apps.folders.serializers import FolderSerializer


class ItemLookupMixin:
    def get_item_with_id(self, request, id=None, idb64=None):
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

    def search_item(self, request, query):
        try:
            files = File.objects.filter(name__icontains=query, owner=request.user)
            folders = Folder.objects.filter(name__icontains=query, owner=request.user)
            return files, folders
        except ObjectDoesNotExist:
            return None, None

    def serialize(self, item, many=False):
        request = getattr(self, "request", None)
        if isinstance(item, File):
            return FileSerializer(item, many=many, context={"request": request})
        elif isinstance(item, Folder):
            return FolderSerializer(item, many=many, context={"request": request})
        else:
            raise ValueError(_("Invalid item"))

    def build_link(self, request, item):
        site = get_current_site(request).domain
        idb64 = self.encode(item.id)
        item_type = item._meta.model.__name__ # Get the model name

        # Dynamically set url type eg ..get-shared-items/files or get-shared-items/folders
        item_type = "files" if item_type == "File" else "folders"

        url = reverse("get-shared-item", args=[item_type, idb64])
        link = f"{request.scheme}://{site}{url}"

        return link

    def encode(self, item_id):
        idb64 = urlsafe_base64_encode(force_bytes(item_id))
        return idb64

    def decode(self, idb64):
        id = force_str(urlsafe_base64_decode(idb64))
        return id



