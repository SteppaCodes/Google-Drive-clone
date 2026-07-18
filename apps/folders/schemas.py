from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FolderCreateSchema(BaseModel):
    name: str
    parent_folder_id: UUID | None = None  # None = root level folder


class FolderUpdateSchema(BaseModel):
    name: str


class FolderResponseSchema(BaseModel):
    id: UUID
    name: str
    owner_id: UUID
    owner_email: str
    parent_folder_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, folder_obj):
        return cls(
            id=folder_obj.id,
            name=folder_obj.name,
            owner_id=folder_obj.owner_id,
            owner_email=folder_obj.owner.email,
            parent_folder_id=folder_obj.folder_id,
            created_at=folder_obj.created_at,
            updated_at=folder_obj.updated_at,
        )


class FolderContentsResponseSchema(BaseModel):
    folder: FolderResponseSchema
    subfolders: list[FolderResponseSchema]
    file_ids: list[UUID]  # File details come from the /files endpoint scoped by folder_id
