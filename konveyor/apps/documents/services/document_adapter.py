"""Django adapter for document service.

This module provides a Django-specific adapter for the core document service.
It handles Django model integration and framework-specific features while
delegating core document processing to the framework-agnostic service.
"""

# Removed ThreadPoolExecutor import (unused)
import logging
import os  # Add os import for content type detection
from typing import Any, BinaryIO, Dict

from django.core.exceptions import ValidationError
from langchain.text_splitter import RecursiveCharacterTextSplitter  # Keep for now

from konveyor.core.documents.document_service import (  # Ensure this points to the core service
    DocumentService,
)

from ..models import Document, DocumentChunk

logger = logging.getLogger(__name__)


class DjangoDocumentService:
    """Django-specific adapter for document processing service."""

    def __init__(self):
        """Initialize the adapter with core document service."""
        self._service = DocumentService()
        # Keep text_splitter initialization for now, as core service doesn't handle chunking orchestration yet.
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )

    def __getattr__(self, name):
        """Delegate unknown attributes to core service."""
        return getattr(self._service, name)

    def process_document(self, file_obj: BinaryIO, filename: str) -> Document:
        """Process a document and create Django model instances.

        Args:
            file_obj: File object to process
            filename: Name of the file

        Returns:
            Document: Created Document instance

        Raises:
            ValidationError: If document processing fails
        """
        try:
            # Determine content type (moved from helper)
            content_type = self._determine_content_type(filename)

            # Create document model instance
            doc = Document.objects.create(
                filename=filename,
                size=file_obj.size if hasattr(file_obj, "size") else 0,
                content_type=content_type,  # Store content type
            )

            # Process with core service
            content, metadata = self._service.parse_file(
                file_obj=file_obj, content_type=content_type
            )

            # Create chunks (logic moved from helper)
            chunk_models = []
            try:
                # Split content into chunks using the text splitter
                texts = self.text_splitter.split_text(content)

                # Create chunk model objects
                for i, text in enumerate(texts):
                    # TODO: Delegate chunk storage to core service if possible in future
                    # For now, adapter creates Django models directly
                    chunk = DocumentChunk.objects.create(
                        document=doc,
                        content=text,  # Storing content directly in model for now
                        sequence=i,
                        # metadata could be added here if needed
                    )
                    chunk_models.append(chunk)
                logger.info(f"Created {len(chunk_models)} chunks for document {doc.id}")

            except Exception as e:
                logger.error(f"Failed to create chunks for document {doc.id}: {str(e)}")
                # Optionally update doc status to FAILED here
                raise  # Re-raise chunking error

            # Update document metadata
            doc.status = "processed"
            doc.metadata = metadata
            doc.save()

            return doc

        except Exception as e:
            logger.error(f"Failed to process document {filename}: {str(e)}")
            raise ValidationError(f"Document processing failed: {str(e)}")

    # Method moved into process_document
    # def _get_content_type(self, filename: str) -> str: ...

    # Method moved into process_document
    # def _create_chunks(self, doc: Document, content: str) -> list: ...

    # Internal helper kept for now as it was moved from _get_content_type
    def _determine_content_type(self, filename: str) -> str:
        """Get content type from filename extension."""
        # Use os.path.splitext for robustness
        _root, ext = os.path.splitext(filename)
        ext = ext.lower()
        content_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".md": "text/markdown",
            ".txt": "text/plain",
        }
        return content_types.get(ext, "application/octet-stream")
