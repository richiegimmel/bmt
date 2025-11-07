from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ResolutionType(str, enum.Enum):
    ORDINARY = "ordinary"
    SPECIAL = "special"
    CONSENT = "consent"
    EMERGENCY = "emergency"


class ResolutionStatus(str, enum.Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    PASSED = "passed"
    FAILED = "failed"
    TABLED = "tabled"
    WITHDRAWN = "withdrawn"


class VoteType(str, enum.Enum):
    AYE = "aye"
    NAY = "nay"
    ABSTAIN = "abstain"
    ABSENT = "absent"


class ActionItemStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class Resolution(Base):
    __tablename__ = "resolutions"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(50), nullable=False, unique=True)  # e.g., "2025-001"
    title = Column(String(500), nullable=False)
    resolution_type = Column(Enum(ResolutionType), nullable=False, default=ResolutionType.ORDINARY)
    status = Column(Enum(ResolutionStatus), nullable=False, default=ResolutionStatus.DRAFT)
    text_content = Column(Text, nullable=False)
    vote_date = Column(Date, nullable=True)
    
    # Foreign keys
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    proposed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Vote tallies
    votes_aye = Column(Integer, default=0)
    votes_nay = Column(Integer, default=0)
    votes_abstain = Column(Integer, default=0)
    votes_absent = Column(Integer, default=0)
    
    # Metadata
    effective_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="resolutions")
    document = relationship("Document")
    proposed_by = relationship("User")
    votes = relationship("ResolutionVote", back_populates="resolution", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="resolution", cascade="all, delete-orphan")


class ResolutionVote(Base):
    __tablename__ = "resolution_votes"

    id = Column(Integer, primary_key=True, index=True)
    resolution_id = Column(Integer, ForeignKey("resolutions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vote = Column(Enum(VoteType), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    resolution = relationship("Resolution", back_populates="votes")
    user = relationship("User")


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ActionItemStatus), nullable=False, default=ActionItemStatus.PENDING)
    
    # Foreign keys
    resolution_id = Column(Integer, ForeignKey("resolutions.id"), nullable=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Dates
    due_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    
    # Metadata
    priority = Column(String(20), nullable=True)  # high, medium, low
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    resolution = relationship("Resolution", back_populates="action_items")
    meeting = relationship("Meeting")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by = relationship("User", foreign_keys=[created_by_id])

