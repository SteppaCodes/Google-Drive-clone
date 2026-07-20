from django.contrib import admin

from .models import (
    Artifact,
    ArtifactChunk,
    ArtifactComment,
    ArtifactPermission,
    ArtifactRelationship,
    ArtifactVersion,
    DecisionArtifact,
    DocumentArtifact,
    MemoryArtifact,
    SkillArtifact,
)


class DocumentInline(admin.StackedInline):
    model = DocumentArtifact
    extra = 0


class VersionInline(admin.TabularInline):
    model = ArtifactVersion
    extra = 0
    readonly_fields = ("version_number", "created_by", "created_at")


@admin.register(Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "lifecycle_state", "owner", "collection", "created_at")
    list_filter = ("type", "lifecycle_state", "embedding_status")
    search_fields = ("title",)
    inlines = [DocumentInline, VersionInline]


@admin.register(ArtifactRelationship)
class ArtifactRelationshipAdmin(admin.ModelAdmin):
    list_display = ("from_artifact", "relation_type", "to_artifact", "created_by")
    list_filter = ("relation_type",)


@admin.register(ArtifactPermission)
class ArtifactPermissionAdmin(admin.ModelAdmin):
    list_display = ("artifact", "principal", "role")
    list_filter = ("role",)


@admin.register(ArtifactComment)
class ArtifactCommentAdmin(admin.ModelAdmin):
    list_display = ("artifact", "author", "created_at")


@admin.register(ArtifactVersion)
class ArtifactVersionAdmin(admin.ModelAdmin):
    list_display = ("artifact", "version_number", "created_by", "created_at")


# Register the extension tables for direct admin access if needed
admin.site.register(DocumentArtifact)
admin.site.register(SkillArtifact)
admin.site.register(DecisionArtifact)
admin.site.register(MemoryArtifact)
admin.site.register(ArtifactChunk)
