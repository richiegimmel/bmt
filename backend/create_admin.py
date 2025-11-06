#!/usr/bin/env python3
"""
Script to create an admin user for the Board Management Tool
"""
import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
# Import all models so SQLAlchemy knows about them
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.models.chat import ChatSession, ChatMessage

def create_admin_user(email: str, username: str, password: str, full_name: str):
    """Create an admin user"""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing_user:
            print(f"Error: User with email '{email}' or username '{username}' already exists")
            return False

        # Create new admin user
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            is_active=True,
            is_admin=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"✓ Admin user created successfully!")
        print(f"  Email: {email}")
        print(f"  Username: {username}")
        print(f"  User ID: {user.id}")
        return True

    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("Board Management Tool - Create Admin User")
    print("=" * 50)

    if len(sys.argv) >= 5:
        email = sys.argv[1]
        username = sys.argv[2]
        password = sys.argv[3]
        full_name = sys.argv[4]
        # Auto-confirm if --yes flag provided or 6 args
        auto_confirm = len(sys.argv) == 6 and sys.argv[5] == '--yes'
    else:
        # Interactive mode
        email = input("Email: ")
        username = input("Username: ")
        password = input("Password: ")
        full_name = input("Full Name: ")
        auto_confirm = False

    print(f"\nCreating admin user: {username} ({email})")

    if auto_confirm:
        confirm = 'y'
    else:
        confirm = input("Continue? (y/n): ")

    if confirm.lower() == 'y':
        create_admin_user(email, username, password, full_name)
    else:
        print("Cancelled.")
