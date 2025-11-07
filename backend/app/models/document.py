from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base


# Association table for document tags (many-to-many)
document_tags = Table(
    'document_tags_association',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('document_tags.id'), primary_key=True)
)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, docx, xlsx
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String, nullable=False)

    # Document content and metadata
    extracted_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)

    # Folder/organization
    folder = Column(String, nullable=True, default="/")
    category_id = Column(Integer, ForeignKey("document_categories.id"), nullable=True)

    # Processing status
    is_processed = Column(Boolean, default=False)
    
    # Version control
    version_number = Column(Integer, default=1)
    is_latest_version = Column(Boolean, default=True)
    parent_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)  # For versions

    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    category = relationship("DocumentCategory", back_populates="documents")
    tags = relationship("DocumentTag", secondary=document_tags, back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan", foreign_keys="DocumentVersion.document_id")
    parent_document = relationship("Document", remote_side=[id], foreign_keys=[parent_document_id])


class DocumentChunk(Base):
    """Stores document chunks with their embeddings for RAG"""
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)

    # Chunk data
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Position in document
    embedding = Column(Vector(1024), nullable=True)  # Claude embeddings are 1024 dimensions

    # Metadata
    page_number = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")


class DocumentCategory(Base):
    """Hierarchical categories for document organization"""
    __tablename__ = "document_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("document_categories.id"), nullable=True)
    icon = Column(String(50), nullable=True)  # Lucide icon name
    color = Column(String(20), nullable=True)  # Color hex code
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0)  # Display order
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    parent = relationship("DocumentCategory", remote_side=[id], back_populates="children")
    children = relationship("DocumentCategory", back_populates="parent", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="category")


class DocumentTag(Base):
    """Tags for flexible document categorization"""
    __tablename__ = "document_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(20), nullable=True)  # Color hex code
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    documents = relationship("Document", secondary=document_tags, back_populates="tags")


class DocumentVersion(Base):
    """Track document versions and changes"""
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    changelog = Column(Text, nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    uploaded_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="versions", foreign_keys=[document_id])
    uploaded_by = relationship("User")
