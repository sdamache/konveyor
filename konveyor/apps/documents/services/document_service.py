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

logger = logging.getLogger(__name__)

class DocumentService:
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
