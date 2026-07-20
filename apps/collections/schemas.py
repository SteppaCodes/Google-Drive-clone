from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CollectionCreateSchema(BaseModel):
    name: str
    parent_id: UUID | None = None  # None = root level collection


class CollectionUpdateSchema(BaseModel):
    name: str


class CollectionResponseSchema(BaseModel):
    id: UUID
    name: str
    owner_id: UUID
    owner_display_name: str
    parent_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, collection_obj):
        return cls(
            id=collection_obj.id,
            name=collection_obj.name,
            owner_id=collection_obj.owner_id,
            owner_display_name=str(collection_obj.owner),
            parent_id=collection_obj.parent_id,
            created_at=collection_obj.created_at,
            updated_at=collection_obj.updated_at,
        )


class CollectionContentsResponseSchema(BaseModel):
    collection: CollectionResponseSchema
    children: list[CollectionResponseSchema]
    artifact_ids: list[UUID]
