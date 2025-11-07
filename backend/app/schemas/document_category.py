from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DocumentCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    order: int = 0


class DocumentCategoryCreate(DocumentCategoryBase):
    pass


class DocumentCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None


class DocumentCategory(DocumentCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    children: List['DocumentCategory'] = []
    document_count: int = 0

    class Config:
        from_attributes = True


class DocumentCategoryTree(DocumentCategory):
    """Category with full tree structure"""
    pass


# Tag schemas
class DocumentTagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = None
    description: Optional[str] = None


class DocumentTagCreate(DocumentTagBase):
    pass


class DocumentTagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = None
    description: Optional[str] = None


class DocumentTag(DocumentTagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

