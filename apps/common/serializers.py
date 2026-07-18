from rest_framework import serializers

from .models import SharedItem, StarredItem


class StarredItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StarredItem
        fields = '__all__'


class UserSharedItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedItem
        fields = '__all__'
