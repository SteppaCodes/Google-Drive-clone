from rest_framework import serializers


from .models import File

class FileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()

    
    class Meta:
        model = File
        fields = [
            'id',
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