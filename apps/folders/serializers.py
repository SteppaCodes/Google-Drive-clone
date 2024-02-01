from rest_framework import serializers
from .models import Folder

from apps.files.serializers import  FileSerializer

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = [
            'id',
            'name',
            'owner'
        ]

        read_only_fields = ['owner', 'id']


class FolderWIthFilesSerializer(serializers.ModelSerializer):
    files = FileSerializer(read_only=True, many=True)

    class Meta:
        model = Folder
        fields = [
            'id', 'name', 'files'
        ]
        
        read_only_fields = ['id']

