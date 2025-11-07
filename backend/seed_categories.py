"""
Seed script to create default document categories for board governance
Run with: python seed_categories.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Import all models first to ensure relationships are set up
from app.models.user import User
from app.models.document import Document, DocumentChunk, DocumentCategory, DocumentTag, DocumentVersion
from app.models.chat import ChatSession, ChatMessage
from app.models.meeting import Meeting, MeetingAttendee, MeetingDocument, AgendaItem
from app.models.board import BoardMember, Committee, CommitteeMember, OfficerRole
from app.models.resolution import Resolution, ResolutionVote, ActionItem
from app.models.compliance import ComplianceItem, ComplianceHistory
from app.models.notification import Notification

from app.core.database import SessionLocal
from datetime import datetime


def create_default_categories():
    """Create default category structure for board governance"""
    db = SessionLocal()
    
    try:
        # Check if categories already exist
        existing = db.query(DocumentCategory).first()
        if existing:
            print("Categories already exist. Skipping seed.")
            return
        
        print("Creating default document categories...")
        
        # Root level categories
        categories_data = [
            {
                "name": "Governing Documents",
                "icon": "Scale",
                "color": "#1e40af",
                "order": 1,
                "description": "Articles, bylaws, and foundational documents",
                "children": [
                    {"name": "Articles of Incorporation", "icon": "FileText", "order": 1},
                    {"name": "Bylaws", "icon": "BookOpen", "order": 2},
                    {"name": "Operating Agreements", "icon": "FileSignature", "order": 3},
                ]
            },
            {
                "name": "Board Meetings",
                "icon": "Users",
                "color": "#059669",
                "order": 2,
                "description": "Board meeting materials and minutes",
                "children": [
                    {"name": "2025", "icon": "Calendar", "order": 1, "children": [
                        {"name": "Q1 2025", "order": 1},
                        {"name": "Q2 2025", "order": 2},
                        {"name": "Q3 2025", "order": 3},
                        {"name": "Q4 2025", "order": 4},
                    ]},
                    {"name": "2024", "icon": "Calendar", "order": 2},
                    {"name": "2023", "icon": "Calendar", "order": 3},
                ]
            },
            {
                "name": "Committee Meetings",
                "icon": "Users2",
                "color": "#7c3aed",
                "order": 3,
                "description": "Committee meeting materials",
                "children": [
                    {"name": "Audit Committee", "icon": "Calculator", "order": 1},
                    {"name": "Compensation Committee", "icon": "DollarSign", "order": 2},
                    {"name": "Governance Committee", "icon": "Shield", "order": 3},
                ]
            },
            {
                "name": "Financial Reports",
                "icon": "TrendingUp",
                "color": "#dc2626",
                "order": 4,
                "description": "Financial statements and reports",
                "children": [
                    {"name": "Monthly Financials", "icon": "BarChart", "order": 1},
                    {"name": "Annual Reports", "icon": "FileText", "order": 2},
                    {"name": "Audits", "icon": "Search", "order": 3},
                    {"name": "Budgets", "icon": "PieChart", "order": 4},
                ]
            },
            {
                "name": "Policies & Procedures",
                "icon": "BookOpen",
                "color": "#ea580c",
                "order": 5,
                "description": "Corporate policies and procedures",
                "children": [
                    {"name": "HR Policies", "icon": "Users", "order": 1},
                    {"name": "Financial Policies", "icon": "DollarSign", "order": 2},
                    {"name": "IT Policies", "icon": "Monitor", "order": 3},
                    {"name": "Safety Policies", "icon": "Shield", "order": 4},
                ]
            },
            {
                "name": "Resolutions",
                "icon": "FileCheck",
                "color": "#0891b2",
                "order": 6,
                "description": "Board resolutions and consent actions"
            },
            {
                "name": "Correspondence",
                "icon": "Mail",
                "color": "#6366f1",
                "order": 7,
                "description": "Letters and communications"
            },
            {
                "name": "Legal Documents",
                "icon": "Gavel",
                "color": "#4b5563",
                "order": 8,
                "description": "Contracts, agreements, and legal filings"
            },
        ]
        
        def create_category(cat_data, parent_id=None):
            """Recursively create categories"""
            category = DocumentCategory(
                name=cat_data["name"],
                parent_id=parent_id,
                icon=cat_data.get("icon"),
                color=cat_data.get("color"),
                description=cat_data.get("description"),
                order=cat_data.get("order", 0)
            )
            db.add(category)
            db.flush()  # Get the ID without committing
            
            print(f"  Created: {cat_data['name']}")
            
            # Create children
            if "children" in cat_data:
                for child_data in cat_data["children"]:
                    create_category(child_data, category.id)
            
            return category
        
        # Create all categories
        for cat_data in categories_data:
            create_category(cat_data)
        
        # Create default tags
        print("\nCreating default document tags...")
        default_tags = [
            {"name": "Urgent", "color": "#dc2626"},
            {"name": "Board Approved", "color": "#059669"},
            {"name": "Draft", "color": "#f59e0b"},
            {"name": "Confidential", "color": "#7c3aed"},
            {"name": "Requires Action", "color": "#dc2626"},
            {"name": "For Review", "color": "#2563eb"},
            {"name": "Historical", "color": "#6b7280"},
        ]
        
        for tag_data in default_tags:
            tag = DocumentTag(**tag_data)
            db.add(tag)
            print(f"  Created tag: {tag_data['name']}")
        
        db.commit()
        print("\n✓ Default categories and tags created successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_default_categories()

