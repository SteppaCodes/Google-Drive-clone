from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from .models import Folder
from apps.files.serializers import  FileSerializer
from apps.common.models import StarredItem


class FolderSerializer(serializers.ModelSerializer):
    starred = serializers.SerializerMethodField()
    
    class Meta:
        model = Folder
        fields = [
            'id',
            'name',
            'owner',
            'starred',
            'folder'
        ]

        read_only_fields = ['owner', 'id']

    def get_starred(self, obj):
        request = self.context.get('request')
        
        if request and request.user.is_authenticated:
            try:
                starred_item = StarredItem.objects.get(user=request.user, 
                                                       content_type=ContentType.objects.get_for_model(obj), object_id=obj.id)
                return True
            except StarredItem.DoesNotExist:
                return False
        return False
        


class FolderWIthFilesSerializer(serializers.ModelSerializer):
    files = FileSerializer(read_only=True, many=True)
    subfolders = FolderSerializer(read_only=True, many=True)

    class Meta:
        model = Folder
        fields = [
            'id', 'name', 'files', 'subfolders'
        ]
        
        read_only_fields = ['id', 'starred']


