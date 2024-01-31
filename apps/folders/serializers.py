from rest_framework import serializers
from .models import Folder


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = [
            'id',
            'name',
            'owner'
        ]

        read_only_fields = ['owner', 'id']