from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FileResponseSchema(BaseModel):
    id: UUID
    name: str
    file_url: str = Field(..., alias="file")
    folder_id: UUID | None = None
    owner_id: UUID
    owner_email: str
    locked_by_id: UUID | None = None
    locked_by_email: str | None = None
    size: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def from_model(cls, file_obj):
        # Helper to construct fields from Django model instances
        file_url = file_obj.file.url if file_obj.file else ""
        try:
            size = file_obj.file.size if file_obj.file else 0
        except Exception:
            size = 0

        return cls(
            id=file_obj.id,
            name=file_obj.name,
            file=file_url,
            folder_id=file_obj.folder_id,
            owner_id=file_obj.owner_id,
            owner_email=file_obj.owner.email,
            locked_by_id=file_obj.locked_by_id,
            locked_by_email=file_obj.locked_by.email if file_obj.locked_by else None,
            size=size,
            created_at=file_obj.created_at,
            updated_at=file_obj.updated_at
        )

class FileVersionResponseSchema(BaseModel):
    id: UUID
    version_number: int
    file_instance_url: str = Field(..., alias="file_instance")
    diff_content: str
    created_by_email: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def from_model(cls, version_obj):
        file_url = version_obj.file_instance.url if version_obj.file_instance else ""
        return cls(
            id=version_obj.id,
            version_number=version_obj.version_number,
            file_instance=file_url,
            diff_content=version_obj.diff_content,
            created_by_email=version_obj.created_by.email if version_obj.created_by else None,
            created_at=version_obj.created_at
        )

class CommentResponseSchema(BaseModel):
    id: UUID
    owner_email: str
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, comment_obj):
        return cls(
            id=comment_obj.id,
            owner_email=comment_obj.owner.email,
            comment=comment_obj.comment,
            created_at=comment_obj.created_at
        )
