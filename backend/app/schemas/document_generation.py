"""
Pydantic schemas for document generation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class GenerateDocumentRequest(BaseModel):
    """Request to generate a document from a template."""

    template_type: str = Field(..., description="Template type (board_resolution, meeting_minutes, notice, consent_action)")
    data: Dict[str, Any] = Field(..., description="Template data/variables")
    format: str = Field(default="docx", description="Output format (docx or pdf)")
    title: str = Field(..., description="Title for the generated document")
    save_to_documents: bool = Field(default=True, description="Whether to save the generated document to the document library")


class GenerateDocumentResponse(BaseModel):
    """Response after generating a document."""

    document_id: Optional[int] = Field(None, description="ID of saved document if save_to_documents=True")
    filename: str = Field(..., description="Generated filename")
    format: str = Field(..., description="Document format")
    size: int = Field(..., description="Document size in bytes")
    download_url: str = Field(..., description="URL to download the document")


class TemplateField(BaseModel):
    """Description of a template field."""

    type: str = Field(..., description="Field type (string, array, etc.)")
    description: str = Field(..., description="Field description")


class TemplateInfo(BaseModel):
    """Information about a document template."""

    template_type: str = Field(..., description="Template type identifier")
    name: str = Field(..., description="Human-readable template name")
    required_fields: List[str] = Field(..., description="Required field names")
    optional_fields: List[str] = Field(..., description="Optional field names")
    fields: Dict[str, TemplateField] = Field(..., description="Field descriptions")


class TemplateListResponse(BaseModel):
    """Response with list of available templates."""

    templates: List[TemplateInfo] = Field(..., description="Available templates")


# Template-specific request models for better validation

class BoardResolutionData(BaseModel):
    """Data for board resolution template."""

    company: Optional[str] = Field(None, description="Company name")
    resolution_number: Optional[str] = Field(None, description="Resolution number")
    date: Optional[str] = Field(None, description="Resolution date")
    resolution_title: str = Field(..., description="Title of the resolution")
    whereas_clauses: Optional[List[str]] = Field(None, description="WHEREAS clauses")
    resolved_clauses: List[str] = Field(..., description="RESOLVED clauses")
    secretary_name: Optional[str] = Field(None, description="Secretary name")


class MeetingMinutesData(BaseModel):
    """Data for meeting minutes template."""

    company: Optional[str] = Field(None, description="Company name")
    date: Optional[str] = Field(None, description="Meeting date")
    time: Optional[str] = Field(None, description="Meeting time")
    location: Optional[str] = Field(None, description="Meeting location")
    attendees: List[str] = Field(..., description="List of attendees")
    absent: Optional[List[str]] = Field(None, description="Absent members")
    guests: Optional[List[str]] = Field(None, description="Guests")
    chair: Optional[str] = Field(None, description="Meeting chair")
    minutes_approval: Optional[List[str]] = Field(None, description="Minutes approval text")
    matters_discussed: List[str] = Field(..., description="Matters discussed")
    resolutions: Optional[List[str]] = Field(None, description="Resolutions adopted")
    adjournment_time: Optional[str] = Field(None, description="Adjournment time")
    secretary_name: Optional[str] = Field(None, description="Secretary name")


class NoticeData(BaseModel):
    """Data for meeting notice template."""

    company: Optional[str] = Field(None, description="Company name")
    date: Optional[str] = Field(None, description="Notice date")
    meeting_date: str = Field(..., description="Meeting date")
    meeting_time: str = Field(..., description="Meeting time")
    meeting_location: str = Field(..., description="Meeting location")
    agenda_items: List[str] = Field(..., description="Agenda items")
    secretary_name: Optional[str] = Field(None, description="Secretary name")


class ConsentActionData(BaseModel):
    """Data for consent action template."""

    company: Optional[str] = Field(None, description="Company name")
    date: Optional[str] = Field(None, description="Effective date")
    resolutions: List[str] = Field(..., description="Resolutions")
    directors: List[str] = Field(..., description="Director names")
