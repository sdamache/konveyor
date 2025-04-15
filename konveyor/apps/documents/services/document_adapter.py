"""Django adapter for document service.

This module provides a Django-specific adapter for the core document service.
It handles Django model integration and framework-specific features while
delegating core document processing to the framework-agnostic service.
"""

from typing import BinaryIO, Dict, Any
from django.core.exceptions import ValidationError
from konveyor.core.documents.document_service import DocumentService
from ..models import Document, DocumentChunk
from langchain.text_splitter import RecursiveCharacterTextSplitter
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class DjangoDocumentService:
    """Django-specific adapter for document processing service."""
    
    def __init__(self):
        """Initialize the adapter with core document service."""
        self._service = DocumentService()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
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
            # Create document model instance
            doc = Document.objects.create(
                filename=filename,
                size=file_obj.size if hasattr(file_obj, 'size') else 0
            )
            
            # Process with core service
            content, metadata = self._service.parse_file(
                file_obj,
                self._get_content_type(filename)
            )
            
            # Create chunks
            chunks = self._create_chunks(doc, content)
            
            # Update document metadata
            doc.status = 'processed'
            doc.metadata = metadata
            doc.save()
            
            return doc
            
        except Exception as e:
            logger.error(f"Failed to process document {filename}: {str(e)}")
            raise ValidationError(f"Document processing failed: {str(e)}")
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type from filename extension."""
        ext = filename.lower().split('.')[-1]
        content_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'md': 'text/markdown',
            'txt': 'text/plain'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def _create_chunks(self, doc: Document, content: str) -> list:
        """Create document chunks from content."""
        chunks = []
        try:
            # Split content into chunks
            texts = self.text_splitter.split_text(content)
            
            # Create chunk objects
            for i, text in enumerate(texts):
                chunk = DocumentChunk.objects.create(
                    document=doc,
                    content=text,
                    sequence=i
                )
                chunks.append(chunk)
                
        except Exception as e:
            logger.error(f"Failed to create chunks for document {doc.id}: {str(e)}")
            raise
            
        return chunks
