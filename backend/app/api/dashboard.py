from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.meeting import Meeting, MeetingStatus
from app.models.resolution import Resolution, ActionItem, ActionItemStatus
from app.models.compliance import ComplianceItem, ComplianceStatus
from app.models.document import Document
from pydantic import BaseModel

router = APIRouter()


class DashboardMetrics(BaseModel):
    upcoming_meetings_count: int
    pending_action_items_count: int
    documents_pending_review: int
    compliance_alerts_count: int


class UpcomingMeeting(BaseModel):
    id: int
    title: str
    meeting_date: str | None
    meeting_time: str | None
    meeting_type: str
    status: str


class RecentActivity(BaseModel):
    id: int
    type: str  # 'document', 'resolution', 'meeting', 'action_item'
    title: str
    description: str
    created_at: str
    icon: str
    url: str


class PendingActionItem(BaseModel):
    id: int
    title: str
    due_date: str | None
    assigned_to: str | None
    status: str
    priority: str | None


class ComplianceAlert(BaseModel):
    id: int
    title: str
    due_date: str
    status: str
    category: str
    days_until_due: int


class DashboardData(BaseModel):
    metrics: DashboardMetrics
    upcoming_meetings: List[UpcomingMeeting]
    recent_activities: List[RecentActivity]
    pending_action_items: List[PendingActionItem]
    compliance_alerts: List[ComplianceAlert]


@router.get("/dashboard", response_model=DashboardData)
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all dashboard data in one request"""
    now = datetime.now()
    thirty_days = now + timedelta(days=30)
    
    # Metrics
    upcoming_meetings = db.query(Meeting).filter(
        and_(
            Meeting.meeting_date >= now,
            Meeting.meeting_date <= thirty_days,
            Meeting.status.in_([MeetingStatus.SCHEDULED, MeetingStatus.DRAFT])
        )
    ).count()
    
    pending_action_items = db.query(ActionItem).filter(
        ActionItem.status.in_([ActionItemStatus.PENDING, ActionItemStatus.IN_PROGRESS])
    ).count()
    
    # Documents not processed or uploaded in last 7 days (as pending review)
    seven_days_ago = now - timedelta(days=7)
    documents_pending = db.query(Document).filter(
        or_(
            Document.is_processed == False,
            Document.created_at >= seven_days_ago
        )
    ).count()
    
    # Compliance items due soon or overdue
    compliance_alerts = db.query(ComplianceItem).filter(
        and_(
            ComplianceItem.due_date <= thirty_days,
            ComplianceItem.status.in_([ComplianceStatus.UPCOMING, ComplianceStatus.DUE_SOON, ComplianceStatus.OVERDUE])
        )
    ).count()
    
    metrics = DashboardMetrics(
        upcoming_meetings_count=upcoming_meetings,
        pending_action_items_count=pending_action_items,
        documents_pending_review=documents_pending,
        compliance_alerts_count=compliance_alerts
    )
    
    # Upcoming meetings (next 3)
    meetings_list = db.query(Meeting).filter(
        and_(
            Meeting.meeting_date >= now,
            Meeting.status.in_([MeetingStatus.SCHEDULED, MeetingStatus.DRAFT])
        )
    ).order_by(Meeting.meeting_date).limit(3).all()
    
    upcoming_meetings_data = [
        UpcomingMeeting(
            id=m.id,
            title=m.title,
            meeting_date=m.meeting_date.isoformat() if m.meeting_date else None,
            meeting_time=m.meeting_time,
            meeting_type=m.meeting_type.value,
            status=m.status.value
        )
        for m in meetings_list
    ]
    
    # Recent activity (last 10 items)
    recent_docs = db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
    recent_resolutions = db.query(Resolution).order_by(Resolution.created_at.desc()).limit(5).all()
    
    activities = []
    for doc in recent_docs:
        activities.append(RecentActivity(
            id=doc.id,
            type='document',
            title=doc.original_filename,
            description=f"Document uploaded by {doc.owner.full_name or doc.owner.username}",
            created_at=doc.created_at.isoformat(),
            icon='FileText',
            url=f'/documents/{doc.id}'
        ))
    
    for res in recent_resolutions:
        activities.append(RecentActivity(
            id=res.id,
            type='resolution',
            title=f"Resolution {res.number}",
            description=res.title,
            created_at=res.created_at.isoformat(),
            icon='FileCheck',
            url=f'/resolutions/{res.id}'
        ))
    
    # Sort by date and limit to 10
    activities.sort(key=lambda x: x.created_at, reverse=True)
    recent_activities_data = activities[:10]
    
    # Pending action items (next 5 by due date)
    action_items_list = db.query(ActionItem).filter(
        ActionItem.status.in_([ActionItemStatus.PENDING, ActionItemStatus.IN_PROGRESS])
    ).order_by(ActionItem.due_date).limit(5).all()
    
    pending_action_items_data = [
        PendingActionItem(
            id=item.id,
            title=item.title,
            due_date=item.due_date.isoformat() if item.due_date else None,
            assigned_to=item.assigned_to.full_name if item.assigned_to else None,
            status=item.status.value,
            priority=item.priority
        )
        for item in action_items_list
    ]
    
    # Compliance alerts (next 5 by due date)
    compliance_items = db.query(ComplianceItem).filter(
        and_(
            ComplianceItem.due_date <= thirty_days,
            ComplianceItem.status.in_([ComplianceStatus.UPCOMING, ComplianceStatus.DUE_SOON, ComplianceStatus.OVERDUE])
        )
    ).order_by(ComplianceItem.due_date).limit(5).all()
    
    compliance_alerts_data = [
        ComplianceAlert(
            id=item.id,
            title=item.title,
            due_date=item.due_date.isoformat(),
            status=item.status.value,
            category=item.category.value,
            days_until_due=(item.due_date - now.date()).days
        )
        for item in compliance_items
    ]
    
    return DashboardData(
        metrics=metrics,
        upcoming_meetings=upcoming_meetings_data,
        recent_activities=recent_activities_data,
        pending_action_items=pending_action_items_data,
        compliance_alerts=compliance_alerts_data
    )

