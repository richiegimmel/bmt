from typing import List, Tuple, Optional
import time
from sqlalchemy.orm import Session
from anthropic import Anthropic

from app.core.config import settings
from app.models.document import DocumentChunk


class EmbeddingService:
    """Service for generating and managing vector embeddings using Claude"""

    def __init__(self):
        """Initialize Anthropic client"""
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Claude model for embeddings

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector (1024 dimensions) or None on error
        """
        try:
            # Note: As of now, Anthropic doesn't have a dedicated embeddings API
            # This is a placeholder for when they release one
            # For now, we'll need to use an alternative approach or wait for the API

            # TODO: Replace with actual Anthropic embeddings API when available
            # For now, we'll return None to indicate embeddings are not yet implemented
            return None

        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once

        Returns:
            List of embedding vectors (or None for failures)
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            for text in batch:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)

                # Rate limiting - small delay between requests
                time.sleep(0.1)

        return embeddings

    def store_chunk_with_embedding(
        self,
        db: Session,
        document_id: int,
        content: str,
        chunk_index: int,
        page_number: Optional[int] = None,
        embedding: Optional[List[float]] = None
    ) -> DocumentChunk:
        """
        Create and store a document chunk with its embedding

        Args:
            db: Database session
            document_id: Parent document ID
            content: Chunk text content
            chunk_index: Index of this chunk
            page_number: Optional page number
            embedding: Optional embedding vector

        Returns:
            Created DocumentChunk
        """
        chunk = DocumentChunk(
            document_id=document_id,
            content=content,
            chunk_index=chunk_index,
            page_number=page_number,
            embedding=embedding
        )

        db.add(chunk)
        db.commit()
        db.refresh(chunk)

        return chunk

    def search_similar_chunks(
        self,
        db: Session,
        query_embedding: List[float],
        limit: int = 10,
        min_score: float = 0.7,
        document_ids: Optional[List[int]] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Search for similar document chunks using vector similarity

        Args:
            db: Database session
            query_embedding: Query vector
            limit: Maximum results to return
            min_score: Minimum similarity score (0-1)
            document_ids: Optional filter by document IDs

        Returns:
            List of (chunk, similarity_score) tuples
        """
        # Build query for vector similarity search using pgvector
        # cosine distance: 1 - cosine_similarity, so lower is better
        # We'll convert to similarity score (higher is better) by: 1 - distance

        query = db.query(DocumentChunk)

        if document_ids:
            query = query.filter(DocumentChunk.document_id.in_(document_ids))

        # Only search chunks that have embeddings
        query = query.filter(DocumentChunk.embedding.isnot(None))

        # Use pgvector's cosine distance operator
        # Note: This requires the pgvector extension and proper column type
        # The actual implementation depends on having the pgvector operators available

        # For now, we'll fetch all and filter (not efficient, but works without embeddings)
        # TODO: Replace with proper pgvector query when embeddings are implemented
        all_chunks = query.limit(limit * 2).all()

        results = []
        for chunk in all_chunks:
            if chunk.embedding:
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                if similarity >= min_score:
                    results.append((chunk, similarity))

        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:limit]

    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score (0-1)
        """
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def get_chunks_for_document(
        self,
        db: Session,
        document_id: int
    ) -> List[DocumentChunk]:
        """
        Get all chunks for a document

        Args:
            db: Database session
            document_id: Document ID

        Returns:
            List of DocumentChunks ordered by chunk_index
        """
        return db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()

    def delete_chunks_for_document(
        self,
        db: Session,
        document_id: int
    ) -> int:
        """
        Delete all chunks for a document

        Args:
            db: Database session
            document_id: Document ID

        Returns:
            Number of chunks deleted
        """
        count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        db.commit()
        return count
