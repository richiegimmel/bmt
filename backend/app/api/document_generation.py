"""
API endpoints for document generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document_generation import (
    GenerateDocumentRequest,
    GenerateDocumentResponse,
    TemplateInfo,
    TemplateListResponse,
    TemplateField
)
from app.services.document_generation import DocumentGenerator
from app.services.document_service import DocumentService

router = APIRouter()


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    current_user: User = Depends(get_current_user)
):
    """
    List all available document templates.

    Returns information about each template including required and optional fields.
    """
    generator = DocumentGenerator()

    templates = []
    for template_type, template_name in generator.TEMPLATE_TYPES.items():
        template_info = generator.get_template_fields(template_type)

        # Convert field definitions to TemplateField objects
        fields = {
            field_name: TemplateField(**field_def)
            for field_name, field_def in template_info["fields"].items()
        }

        templates.append(TemplateInfo(
            template_type=template_type,
            name=template_name,
            required_fields=template_info["required"],
            optional_fields=template_info["optional"],
            fields=fields
        ))

    return TemplateListResponse(templates=templates)


@router.post("/generate", response_model=GenerateDocumentResponse)
async def generate_document(
    request: GenerateDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a document from a template.

    Args:
        request: Document generation request with template type and data

    Returns:
        Generated document information and download URL
    """
    try:
        # Generate the document
        generator = DocumentGenerator()
        document_bytes = generator.generate_document(
            template_type=request.template_type,
            data=request.data,
            format=request.format
        )

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{request.title.replace(' ', '_')}_{timestamp}.{request.format}"

        document_id = None
        if request.save_to_documents:
            # Save to document library
            doc_service = DocumentService()

            # Save file to storage
            file_path = doc_service._save_file(
                file_content=document_bytes,
                filename=filename,
                original_filename=filename
            )

            # Create document record
            document = Document(
                title=request.title,
                description=f"Generated {generator.TEMPLATE_TYPES.get(request.template_type, request.template_type)}",
                file_name=filename,
                file_path=file_path,
                file_size=len(document_bytes),
                mime_type="application/pdf" if request.format == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                uploaded_by=current_user.id,
                processed=False  # Generated documents don't need processing
            )

            db.add(document)
            db.commit()
            db.refresh(document)

            document_id = document.id

        return GenerateDocumentResponse(
            document_id=document_id,
            filename=filename,
            format=request.format,
            size=len(document_bytes),
            download_url=f"/api/v1/documents/{document_id}/download" if document_id else f"/api/v1/document-generation/download/{filename}"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate document: {str(e)}"
        )


@router.post("/generate/download", response_class=Response)
async def generate_and_download(
    request: GenerateDocumentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a document and return it directly for download (without saving to library).

    Args:
        request: Document generation request

    Returns:
        Generated document as downloadable file
    """
    try:
        # Generate the document
        generator = DocumentGenerator()
        document_bytes = generator.generate_document(
            template_type=request.template_type,
            data=request.data,
            format=request.format
        )

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{request.title.replace(' ', '_')}_{timestamp}.{request.format}"

        # Determine content type
        content_type = (
            "application/pdf" if request.format == "pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        return Response(
            content=document_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate document: {str(e)}"
        )


@router.get("/templates/{template_type}", response_model=TemplateInfo)
async def get_template_info(
    template_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific template.

    Args:
        template_type: The template type identifier

    Returns:
        Template information including all fields
    """
    try:
        generator = DocumentGenerator()

        if template_type not in generator.TEMPLATE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template type '{template_type}' not found"
            )

        template_name = generator.TEMPLATE_TYPES[template_type]
        template_info = generator.get_template_fields(template_type)

        # Convert field definitions to TemplateField objects
        fields = {
            field_name: TemplateField(**field_def)
            for field_name, field_def in template_info["fields"].items()
        }

        return TemplateInfo(
            template_type=template_type,
            name=template_name,
            required_fields=template_info["required"],
            optional_fields=template_info["optional"],
            fields=fields
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template info: {str(e)}"
        )
