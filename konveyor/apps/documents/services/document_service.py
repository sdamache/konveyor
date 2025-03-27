import os
from typing import BinaryIO, List, Dict, Any
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.conf import settings
from ..models import Document, DocumentChunk
import logging
from konveyor.config.azure import AzureConfig
from langchain.text_splitter import RecursiveCharacterTextSplitter
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from bs4 import BeautifulSoup
import docx
import markdown
from ..config import DOCUMENT_SETTINGS
from concurrent.futures import ThreadPoolExecutor
from django.utils import timezone
from azure.storage.blob import BlobServiceClient, ContentSettings
import uuid
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from azure.core.exceptions import AzureError

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for handling document operations with blob storage."""
    
    def __init__(self):
        self.azure = AzureConfig()
        endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        if not endpoint:
            raise ImproperlyConfigured("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT environment variable is required")
            
        try:
            self.doc_intelligence_client = DocumentIntelligenceClient(
                endpoint=endpoint,
                credential=self.azure.credential
            )
        except Exception as e:
            logger.error(f"Failed to initialize Document Intelligence client: {str(e)}")
            raise ImproperlyConfigured(f"Document Intelligence client configuration is invalid: {str(e)}")
            
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
        
        self.blob_service_client = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
    
    def process_document(self, file_obj: BinaryIO, filename: str, title: str = None) -> Document:
        try:
            # Get file type
            file_type = os.path.splitext(filename)[1][1:].lower()
            
            # Initialize parser
            parser = DocumentParser(self.doc_intelligence_client)
            
            # Parse document
            content, metadata = parser.parse_file(file_obj, file_type)
            
            # Create document
            document = Document.objects.create(
                title=title or os.path.splitext(filename)[0],
                file=file_obj,
                file_type=file_type
            )
            
            # Split into chunks
            chunks = self.text_splitter.create_documents(
                [content],
                metadatas=[metadata]
            )
            
            # Save chunks
            for i, chunk in enumerate(chunks):
                DocumentChunk.objects.create(
                    document=document,
                    content=chunk.page_content,
                    chunk_index=i,
                    metadata={**chunk.metadata, 'chunk_index': i}
                )
            
            # Upload to Azure Storage
            self._upload_to_storage(document, file_obj)
            
            # Index in Search
            self._index_chunks(document)
            
            return document
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            raise ValidationError(f"Failed to process document: {str(e)}")
    
    def search_documents(self, query: str, top: int = 10) -> List[Dict[str, Any]]:
        try:
            results = self.azure.search.search(
                search_text=query,
                top=top,
                include_total_count=True
            )
            return [dict(result) for result in results]
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise ValidationError(f"Failed to search documents: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(AzureError),
        reraise=True
    )
    def store_document(self, file: BinaryIO, filename: str, content_type: str) -> Document:
        """
        Store a document in blob storage and create database record.
        
        Args:
            file: File-like object containing the document
            filename: Original filename
            content_type: MIME type of the document
            
        Returns:
            Created Document instance
        """
        try:
            document_id = str(uuid.uuid4())
            blob_path = f"documents/{document_id}/{filename}"
            
            # Upload to blob storage with retry logic
            blob_client = self._get_blob_client(blob_path)
            blob_client.upload_blob(
                file,
                content_settings=ContentSettings(content_type=content_type),
                overwrite=True
            )
            
            # Create database record
            document = Document.objects.create(
                id=document_id,
                title=filename,
                blob_path=blob_path,
                content_type=content_type,
                status='PENDING'
            )
            
            logger.info(f"Stored document {document_id} in blob storage: {blob_path}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to store document {filename}: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(AzureError),
        reraise=True
    )
    def store_document_chunk(
        self, 
        document: Document, 
        content: str, 
        chunk_index: int, 
        metadata: Dict[str, Any]
    ) -> DocumentChunk:
        """
        Store a document chunk in blob storage.
        
        Args:
            document: Parent Document instance
            content: Chunk content
            chunk_index: Index of the chunk
            metadata: Additional metadata for the chunk
            
        Returns:
            Created DocumentChunk instance
        """
        try:
            chunk_id = str(uuid.uuid4())
            blob_path = f"chunks/{document.id}/{chunk_id}.txt"
            
            # Upload to blob storage with retry logic
            blob_client = self._get_blob_client(blob_path)
            blob_client.upload_blob(
                content,
                content_settings=ContentSettings(
                    content_type='text/plain',
                    content_encoding='utf-8'
                ),
                overwrite=True
            )
            
            # Create database record
            chunk = DocumentChunk.objects.create(
                id=chunk_id,
                document=document,
                chunk_index=chunk_index,
                blob_path=blob_path,
                metadata=metadata
            )
            
            logger.info(f"Stored chunk {chunk_id} for document {document.id}")
            return chunk
            
        except Exception as e:
            logger.error(f"Failed to store chunk for document {document.id}: {str(e)}")
            raise
    
    def _get_blob_client(self, blob_path: str):
        """
        Get a blob client for the given path.
        
        Args:
            blob_path: Path to the blob
            
        Returns:
            BlobClient instance
        """
        return self.blob_service_client.get_container_client(
            self.container_name
        ).get_blob_client(blob_path)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(AzureError),
        reraise=True
    )
    def get_document_content(self, document: Document) -> bytes:
        """
        Retrieve document content from blob storage.
        
        Args:
            document: Document instance
            
        Returns:
            Document content as bytes
        """
        try:
            blob_client = self._get_blob_client(document.blob_path)
            return blob_client.download_blob().readall()
            
        except Exception as e:
            logger.error(f"Failed to retrieve document {document.id}: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(AzureError),
        reraise=True
    )
    def get_chunk_content(self, chunk: DocumentChunk) -> str:
        """
        Retrieve chunk content from blob storage.
        
        Args:
            chunk: DocumentChunk instance
            
        Returns:
            Chunk content as string
        """
        try:
            blob_client = self._get_blob_client(chunk.blob_path)
            return blob_client.download_blob().readall().decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to retrieve chunk {chunk.id}: {str(e)}")
            raise
    
    def delete_document(self, document: Document) -> None:
        """
        Delete a document and all its chunks from blob storage.
        
        Args:
            document: Document instance to delete
        """
        try:
            # Delete document blob
            document_blob_client = self._get_blob_client(document.blob_path)
            document_blob_client.delete_blob(delete_snapshots="include")
            
            # Delete all chunk blobs
            container_client = self.blob_service_client.get_container_client(self.container_name)
            chunk_prefix = f"chunks/{document.id}/"
            blobs_to_delete = container_client.list_blobs(name_starts_with=chunk_prefix)
            
            for blob in blobs_to_delete:
                container_client.delete_blob(blob.name, delete_snapshots="include")
            
            # Delete database records (will cascade to chunks)
            document.delete()
            
            logger.info(f"Deleted document {document.id} and all its chunks")
            
        except Exception as e:
            logger.error(f"Failed to delete document {document.id}: {str(e)}")
            raise

class DocumentParser:
    def __init__(self, doc_intelligence_client=None):
        self.doc_intelligence_client = doc_intelligence_client
        
    def parse_file(self, file_obj: BinaryIO, file_type: str) -> tuple[str, dict]:
        """Parse file and return (content, metadata)"""
        parsers = {
            'pdf': self._parse_pdf,
            'docx': self._parse_docx,
            'md': self._parse_markdown,
            'txt': self._parse_text
        }
        
        if file_type not in parsers:
            raise ValidationError(f"Unsupported file type: {file_type}")
            
        return parsers[file_type](file_obj)
    
    def _parse_pdf(self, file_obj: BinaryIO) -> tuple[str, dict]:
        try:
            poller = self.doc_intelligence_client.begin_analyze_document(
                "prebuilt-read",
                body=file_obj,
                pages="1-100"
            )
            result = poller.result()
            
            # Extract text and metadata
            pages_content = []
            for page in result.pages:
                page_text = " ".join([line.content for line in page.lines])
                pages_content.append(page_text)
                
            metadata = {
                'page_count': len(result.pages),
                'language': result.languages[0] if result.languages else None,
                'styles': [style.name for style in result.styles] if hasattr(result, 'styles') else []
            }
            
            return "\n\n".join(pages_content), metadata
            
        except Exception as e:
            logger.error(f"PDF parsing error: {str(e)}")
            raise
    
    def _parse_docx(self, file_obj: BinaryIO) -> tuple[str, dict]:
        doc = docx.Document(file_obj)
        content = "\n".join([p.text for p in doc.paragraphs])
        metadata = {
            'page_count': len(doc.sections),
            'title': doc.core_properties.title,
            'author': doc.core_properties.author,
            'created': doc.core_properties.created,
            'modified': doc.core_properties.modified
        }
        return content, metadata
        
    def _parse_markdown(self, file_obj: BinaryIO) -> tuple[str, dict]:
        content = file_obj.read().decode('utf-8')
        html = markdown.markdown(content)
        # Convert HTML to plain text
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        metadata = {
            'page_count': 1,
            'format': 'markdown'
        }
        return text, metadata
        
    def _parse_text(self, file_obj: BinaryIO) -> tuple[str, dict]:
        content = file_obj.read().decode('utf-8')
        metadata = {
            'page_count': 1,
            'format': 'plain_text'
        }
        return content, metadata

class BatchProcessor:
    def __init__(self, doc_service: DocumentService, max_workers: int = 3):
        self.doc_service = doc_service
        self.max_workers = max_workers
        
    def process_batch(self, files: List[Dict]) -> Dict[str, Any]:
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(
                    self.doc_service.process_document,
                    file['obj'],
                    file['name']
                ): file['name']
                for file in files
            }
            
            for future in futures.as_completed(future_to_file):
                filename = future_to_file[future]
                try:
                    doc = future.result()
                    results[filename] = {
                        'status': 'success',
                        'document_id': str(doc.id)
                    }
                except Exception as e:
                    results[filename] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    
        return results
