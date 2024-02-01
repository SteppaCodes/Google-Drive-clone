from rest_framework import serializers

from .models import StarredItem


class StarredItemsSerielizer(serializers.ModelSerializer):
    class Meta:
        model = StarredItem
        fields = '__all__'

    