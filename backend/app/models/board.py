from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class MemberStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EMERITUS = "emeritus"


class CommitteeType(str, enum.Enum):
    STANDING = "standing"
    AD_HOC = "ad_hoc"
    SPECIAL = "special"


class CommitteeRole(str, enum.Enum):
    CHAIR = "chair"
    VICE_CHAIR = "vice_chair"
    MEMBER = "member"
    SECRETARY = "secretary"


class BoardMember(Base):
    __tablename__ = "board_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    position = Column(String(100), nullable=True)  # Chairman, Director, etc.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    term_length = Column(Integer, nullable=True)  # in years
    status = Column(Enum(MemberStatus), nullable=False, default=MemberStatus.ACTIVE)
    bio = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="board_member")
    committee_memberships = relationship("CommitteeMember", back_populates="board_member", cascade="all, delete-orphan")
    officer_roles = relationship("OfficerRole", back_populates="board_member", cascade="all, delete-orphan")


class Committee(Base):
    __tablename__ = "committees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    committee_type = Column(Enum(CommitteeType), nullable=False, default=CommitteeType.STANDING)
    chair_id = Column(Integer, ForeignKey("board_members.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    charter = Column(Text, nullable=True)  # Committee charter/mission
    meeting_frequency = Column(String(100), nullable=True)  # e.g., "Monthly", "Quarterly"
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    chair = relationship("BoardMember", foreign_keys=[chair_id])
    members = relationship("CommitteeMember", back_populates="committee", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="committee")


class CommitteeMember(Base):
    __tablename__ = "committee_members"

    id = Column(Integer, primary_key=True, index=True)
    committee_id = Column(Integer, ForeignKey("committees.id"), nullable=False)
    board_member_id = Column(Integer, ForeignKey("board_members.id"), nullable=False)
    role = Column(Enum(CommitteeRole), nullable=False, default=CommitteeRole.MEMBER)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    committee = relationship("Committee", back_populates="members")
    board_member = relationship("BoardMember", back_populates="committee_memberships")


class OfficerRole(Base):
    __tablename__ = "officer_roles"

    id = Column(Integer, primary_key=True, index=True)
    board_member_id = Column(Integer, ForeignKey("board_members.id"), nullable=False)
    title = Column(String(100), nullable=False)  # Chairman, President, Secretary, Treasurer, etc.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=True)
    responsibilities = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    board_member = relationship("BoardMember", back_populates="officer_roles")

