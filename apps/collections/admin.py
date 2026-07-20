from django.contrib import admin

from .models import Collection


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "parent", "created_at")
    search_fields = ("name",)
    list_filter = ("created_at",)
