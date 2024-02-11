from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from .models import File, Comment
from apps.common.models import StarredItem


class FileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    size = serializers.SerializerMethodField()
    starred = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            "id",
            "starred",
            "name",
            "file",
            "name",
            "owner",
            "folder",
            "size",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "size", "owner", "name", "created_at", "updateed_at"]

    def validate(self, attrs):
        file = attrs.get("file")

        if file and hasattr(file, "name"):
            name = file.name
            attrs["name"] = name

        return super().validate(attrs)

    def get_size(self, obj):
        file_size = 0
        if obj.file and hasattr(obj.file, "size"):
            file_size = obj.file.size
        return file_size

    def get_starred(self, obj):
        request = self.context.get("request")
        print(request)
        if request and request.user.is_authenticated:
            try:
                starred_item = StarredItem.objects.get(
                    user=request.user,
                    content_type=ContentType.objects.get_for_model(obj),
                    object_id=obj.id,
                )
                return True
            except StarredItem.DoesNotExist:
                return False
        return False


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            "id",
            "owner",
            "comment",
            "file",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "owner"]


class FileWithCommentsSerialzer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True)

    class Meta:
        model = File
        fields = [
            "name",
            "owner",
            "comments",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "comments", "owner"]
