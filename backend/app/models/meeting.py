from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class MeetingType(str, enum.Enum):
    REGULAR = "regular"
    SPECIAL = "special"
    COMMITTEE = "committee"
    ANNUAL = "annual"


class MeetingStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AttendanceStatus(str, enum.Enum):
    INVITED = "invited"
    CONFIRMED = "confirmed"
    ATTENDED = "attended"
    ABSENT = "absent"
    EXCUSED = "excused"


class DocumentRole(str, enum.Enum):
    PRE_READ = "pre_read"
    AGENDA = "agenda"
    MINUTES = "minutes"
    RESOLUTION = "resolution"
    SUPPORTING = "supporting"


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    meeting_type = Column(Enum(MeetingType), nullable=False, default=MeetingType.REGULAR)
    meeting_date = Column(DateTime, nullable=True)
    meeting_time = Column(String(50), nullable=True)  # Store as string for flexibility
    location = Column(String(500), nullable=True)
    virtual_link = Column(String(500), nullable=True)
    status = Column(Enum(MeetingStatus), nullable=False, default=MeetingStatus.DRAFT)
    description = Column(Text, nullable=True)
    agenda = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Foreign keys
    minutes_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    attendees = relationship("MeetingAttendee", back_populates="meeting", cascade="all, delete-orphan")
    documents = relationship("MeetingDocument", back_populates="meeting", cascade="all, delete-orphan")
    agenda_items = relationship("AgendaItem", back_populates="meeting", cascade="all, delete-orphan")
    resolutions = relationship("Resolution", back_populates="meeting")
    minutes_document = relationship("Document", foreign_keys=[minutes_document_id])
    committee = relationship("Committee", back_populates="meetings")
    created_by = relationship("User", foreign_keys=[created_by_id])


class MeetingAttendee(Base):
    __tablename__ = "meeting_attendees"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=True)  # member, observer, presenter, etc.
    attendance_status = Column(Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.INVITED)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="attendees")
    user = relationship("User")


class MeetingDocument(Base):
    __tablename__ = "meeting_documents"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    document_role = Column(Enum(DocumentRole), nullable=False, default=DocumentRole.SUPPORTING)
    order = Column(Integer, nullable=True)  # For ordering documents in the meeting packet
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="documents")
    document = relationship("Document")


class AgendaItem(Base):
    __tablename__ = "agenda_items"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    order = Column(Integer, nullable=False, default=0)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    time_allocated = Column(Integer, nullable=True)  # in minutes
    presenter = Column(String(255), nullable=True)
    related_document_ids = Column(JSON, nullable=True)  # Array of document IDs
    completed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="agenda_items")

