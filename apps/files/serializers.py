from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from .models import File
from apps.common.models import StarredItem

class FileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    starred = serializers.SerializerMethodField()
    
    class Meta:
        model = File
        fields = [
            'id',
            'starred',
            'name',
            'file',
            'name',
            'owner',
            'folder',
            'size',
            'created_at',
            'updated_at'
        ]
        read_only_fields =['id', 'size', 'owner', 
                           'created_at', 'updateed_at']
    
    def get_name(self, obj):
        file_name = ''
        if obj.file and hasattr(obj.file, 'name'):
            file_name = obj.file.name
        return file_name

    def get_size(self, obj):
        file_size = 0
        if obj.file and hasattr(obj.file, 'size'):
            file_size = obj.file.size
        return file_size
    

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
