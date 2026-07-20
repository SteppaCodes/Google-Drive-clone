from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.artifacts.models import Artifact
from apps.collections.models import Collection


class ArtifactDRFSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artifact
        fields = '__all__'


class CollectionDRFSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = '__all__'


class ItemLookupMixin:
    def get_item_with_id(self, request, id=None, idb64=None):
        if idb64:
            id = force_str(urlsafe_base64_decode(idb64))
        try:
            item = Artifact.objects.get(id=id)
            return item
        except Artifact.DoesNotExist:
            try:
                item = Collection.objects.get(id=id)
                return item
            except Collection.DoesNotExist:
                return None

    def search_item(self, request, query):
        try:
            # We filter by owner. Since owner is now a Principal, we resolve request.user.principal
            principal = getattr(request.user, "principal", None)
            if not principal:
                return Artifact.objects.none(), Collection.objects.none()
            artifacts = Artifact.objects.filter(title__icontains=query, owner=principal)
            collections = Collection.objects.filter(name__icontains=query, owner=principal)
            return artifacts, collections
        except ObjectDoesNotExist:
            return None, None

    def serialize(self, item, many=False):
        request = getattr(self, "request", None)
        if isinstance(item, Artifact):
            return ArtifactDRFSerializer(item, many=many, context={"request": request})
        elif isinstance(item, Collection):
            return CollectionDRFSerializer(item, many=many, context={"request": request})
        else:
            raise ValueError(_("Invalid item"))

    def build_link(self, request, item):
        site = get_current_site(request).domain
        idb64 = self.encode(item.id)
        item_type = item._meta.model.__name__ # Get the model name

        # Dynamically set url type
        item_type = "artifacts" if item_type == "Artifact" else "collections"

        url = reverse("get-shared-item", args=[item_type, idb64])
        link = f"{request.scheme}://{site}{url}"

        return link

    def encode(self, item_id):
        idb64 = urlsafe_base64_encode(force_bytes(item_id))
        return idb64

    def decode(self, idb64):
        id = force_str(urlsafe_base64_decode(idb64))
        return id
