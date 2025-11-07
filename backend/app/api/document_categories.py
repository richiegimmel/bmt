from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document import DocumentCategory, DocumentTag
from app.schemas.document_category import (
    DocumentCategory as DocumentCategorySchema,
    DocumentCategoryCreate,
    DocumentCategoryUpdate,
    DocumentTag as DocumentTagSchema,
    DocumentTagCreate,
    DocumentTagUpdate
)
from sqlalchemy import func

router = APIRouter()


def build_category_tree(categories: List[DocumentCategory], parent_id: int = None) -> List[dict]:
    """Build hierarchical category tree"""
    tree = []
    for category in categories:
        if category.parent_id == parent_id:
            category_dict = {
                "id": category.id,
                "name": category.name,
                "parent_id": category.parent_id,
                "icon": category.icon,
                "color": category.color,
                "description": category.description,
                "order": category.order,
                "created_at": category.created_at,
                "updated_at": category.updated_at,
                "document_count": len(category.documents),
                "children": build_category_tree(categories, category.id)
            }
            tree.append(category_dict)
    return sorted(tree, key=lambda x: x["order"])


@router.get("/categories", response_model=List[DocumentCategorySchema])
def list_categories(
    flat: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all document categories"""
    categories = db.query(DocumentCategory).order_by(DocumentCategory.order).all()
    
    if flat:
        # Return flat list
        return [{
            "id": cat.id,
            "name": cat.name,
            "parent_id": cat.parent_id,
            "icon": cat.icon,
            "color": cat.color,
            "description": cat.description,
            "order": cat.order,
            "created_at": cat.created_at,
            "updated_at": cat.updated_at,
            "children": [],
            "document_count": len(cat.documents)
        } for cat in categories]
    else:
        # Return hierarchical tree
        return build_category_tree(categories)


@router.post("/categories", response_model=DocumentCategorySchema, status_code=status.HTTP_201_CREATED)
def create_category(
    category: DocumentCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new document category"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create categories"
        )
    
    # Validate parent exists if specified
    if category.parent_id:
        parent = db.query(DocumentCategory).filter(DocumentCategory.id == category.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )
    
    db_category = DocumentCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return {
        **db_category.__dict__,
        "children": [],
        "document_count": 0
    }


@router.get("/categories/{category_id}", response_model=DocumentCategorySchema)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific category"""
    category = db.query(DocumentCategory).filter(DocumentCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return {
        **category.__dict__,
        "children": [],
        "document_count": len(category.documents)
    }


@router.put("/categories/{category_id}", response_model=DocumentCategorySchema)
def update_category(
    category_id: int,
    category_update: DocumentCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a category"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update categories"
        )
    
    db_category = db.query(DocumentCategory).filter(DocumentCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Update fields
    update_data = category_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    
    return {
        **db_category.__dict__,
        "children": [],
        "document_count": len(db_category.documents)
    }


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a category"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete categories"
        )
    
    category = db.query(DocumentCategory).filter(DocumentCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if category has documents
    if len(category.documents) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with documents. Move documents first."
        )
    
    # Check if category has children
    if len(category.children) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with subcategories. Delete subcategories first."
        )
    
    db.delete(category)
    db.commit()


# Tags endpoints
@router.get("/tags", response_model=List[DocumentTagSchema])
def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all document tags"""
    tags = db.query(DocumentTag).order_by(DocumentTag.name).all()
    return tags


@router.post("/tags", response_model=DocumentTagSchema, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag: DocumentTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new document tag"""
    # Check if tag already exists
    existing = db.query(DocumentTag).filter(DocumentTag.name == tag.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists"
        )
    
    db_tag = DocumentTag(**tag.model_dump())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a tag"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete tags"
        )
    
    tag = db.query(DocumentTag).filter(DocumentTag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    db.delete(tag)
    db.commit()

