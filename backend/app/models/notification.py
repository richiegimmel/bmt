from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class NotificationType(str, enum.Enum):
    MEETING_INVITE = "meeting_invite"
    MEETING_REMINDER = "meeting_reminder"
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_SHARED = "document_shared"
    ACTION_ITEM_ASSIGNED = "action_item_assigned"
    ACTION_ITEM_DUE = "action_item_due"
    COMPLIANCE_ALERT = "compliance_alert"
    RESOLUTION_VOTE = "resolution_vote"
    MESSAGE = "message"
    SYSTEM = "system"


class NotificationPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.NORMAL)
    
    # Content
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(500), nullable=True)  # URL to navigate when clicked
    action_label = Column(String(100), nullable=True)  # Label for action button
    
    # Additional data
    extra_data = Column(JSON, nullable=True)  # Additional data (meeting_id, document_id, etc.)
    
    # Status
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    # Email notification
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Auto-delete after expiration
    
    # Relationships
    user = relationship("User", back_populates="notifications")

