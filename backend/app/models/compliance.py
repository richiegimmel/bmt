from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Date, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ComplianceCategory(str, enum.Enum):
    FILING = "filing"
    POLICY = "policy"
    TRAINING = "training"
    MEETING = "meeting"
    CERTIFICATION = "certification"
    INSURANCE = "insurance"
    AUDIT = "audit"


class ComplianceStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    COMPLETED = "completed"
    NOT_APPLICABLE = "not_applicable"


class RecurrenceType(str, enum.Enum):
    NONE = "none"
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    BIANNUAL = "biannual"


class ComplianceItem(Base):
    __tablename__ = "compliance_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(ComplianceCategory), nullable=False)
    due_date = Column(Date, nullable=False)
    recurrence = Column(Enum(RecurrenceType), nullable=False, default=RecurrenceType.NONE)
    status = Column(Enum(ComplianceStatus), nullable=False, default=ComplianceStatus.UPCOMING)
    
    # Assignment
    responsible_party_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Details
    requirements = Column(Text, nullable=True)  # What needs to be done
    consequences = Column(Text, nullable=True)  # Consequences of non-compliance
    reference_url = Column(String(500), nullable=True)  # External reference/law
    notes = Column(Text, nullable=True)
    
    # Alerts
    alert_days_before = Column(Integer, default=30)  # Days before due date to alert
    is_critical = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    responsible_party = relationship("User")
    history = relationship("ComplianceHistory", back_populates="compliance_item", cascade="all, delete-orphan")


class ComplianceHistory(Base):
    __tablename__ = "compliance_history"

    id = Column(Integer, primary_key=True, index=True)
    compliance_item_id = Column(Integer, ForeignKey("compliance_items.id"), nullable=False)
    completed_date = Column(Date, nullable=False)
    completed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Proof of completion
    proof_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    compliance_item = relationship("ComplianceItem", back_populates="history")
    completed_by = relationship("User")
    proof_document = relationship("Document")

