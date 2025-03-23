import os
import sys
import json
import logging  # Add this import
from azure.identity import DefaultAzureCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import Union, BinaryIO
import docx
import markdown
from dataclasses import dataclass
from datetime import datetime
from queue import Queue, Empty
from threading import Thread
from typing import List, Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def process_document():
    """Process the test.pdf document and print the extracted chunks."""
    
    # Initialize Azure Document Intelligence client
    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
    
    if not endpoint or not key:
        raise ValueError(
            "Required environment variables not set:\n"
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT\n"
            "AZURE_DOCUMENT_INTELLIGENCE_API_KEY"
        )
    
    # Set file path
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test.pdf")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"test.pdf not found at {file_path}")
    
    # Verify file size
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise ValueError(f"File {file_path} is empty")
    
    print(f"Processing document: {file_path} (size: {file_size} bytes)")
    
    try:
        # Initialize client with AzureKeyCredential
        doc_client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
        
        # Read and process document
        with open(file_path, "rb") as doc:
            doc_content = doc.read()
            print("Starting document analysis...")
            
            try:
                # Updated API call with correct model ID
                poller = doc_client.begin_analyze_document(
                    "prebuilt-read",     # Changed from "prebuilt-document" to "prebuilt-read"
                    body=doc_content,
                    pages="1-100"
                )
                print("Waiting for analysis to complete...")
                result = poller.result()
                
            except AzureError as ae:
                print(f"Azure API Error: {str(ae)}")
                raise
            except Exception as e:
                print(f"Document processing error: {str(e)}")
                raise
        
        # Check if content was extracted
        if not result:
            print("Warning: No results returned from the API")
            return
            
        # Extract text content page by page (matching service implementation)
        text_content = []
        for page_num, page in enumerate(result.pages):
            print(f"Processing page #{page.page_number}")
            page_content = f"page {page_num + 1}: "
            for line in page.lines:
                page_content += line.content
            text_content.append(page_content)
            
        # Join all pages
        full_text = " ".join(text_content)
        if not full_text:
            print("Warning: No text content extracted")
            return
            
        # Initialize text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
        
        # Split into chunks
        chunks = text_splitter.create_documents([full_text])
        
        print(f"\nSplit into {len(chunks)} chunks:")
        print("-" * 50)
        for i, chunk in enumerate(chunks):
            print(f"\nChunk {i + 1}:")
            print(chunk.page_content[:200] + "..." if len(chunk.page_content) > 200 else chunk.page_content)

    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        raise

class DocumentParser:
    def parse_file(self, file_path: str) -> str:
        """Parse different file types and return text content."""
        file_extension = file_path.lower().split('.')[-1]
        
        parsers = {
            'pdf': self._parse_pdf,
            'docx': self._parse_docx,
            'md': self._parse_markdown,
            'txt': self._parse_text
        }
        
        if file_extension not in parsers:
            raise ValueError(f"Unsupported file type: {file_extension}")
            
        return parsers[file_extension](file_path)
    
    def _parse_pdf(self, file_path: str) -> str:
        # Current PDF processing logic using Azure Document Intelligence
        # Move existing PDF processing code here
        pass
        
    def _parse_docx(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
    def _parse_markdown(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            html = markdown.markdown(content)
            # Convert HTML to plain text (you might want to use BeautifulSoup)
            return html
            
    def _parse_text(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

@dataclass
class DocumentMetadata:
    file_name: str
    file_type: str
    creation_date: datetime
    modified_date: datetime
    size_bytes: int
    page_count: int
    author: str = None
    title: str = None
    
def extract_metadata(file_path: str) -> DocumentMetadata:
    """Extract metadata from document."""
    file_stats = os.stat(file_path)
    file_name = os.path.basename(file_path)
    file_type = file_name.split('.')[-1].lower()
    
    metadata = DocumentMetadata(
        file_name=file_name,
        file_type=file_type,
        creation_date=datetime.fromtimestamp(file_stats.st_ctime),
        modified_date=datetime.fromtimestamp(file_stats.st_mtime),
        size_bytes=file_stats.st_size,
        page_count=0  # Will be updated based on document type
    )
    
    return metadata

@dataclass
class ProcessedDocument:
    content: str
    metadata: DocumentMetadata
    chunks: list[str]
    page_map: dict[int, str]  # Maps page numbers to content
    error_log: list[str]
    processing_status: str

class DocumentProcessingQueue:
    def __init__(self, num_workers: int = 3, timeout: int = 300):
        self.queue = Queue()
        self.results = {}
        self.num_workers = num_workers
        self.timeout = timeout  # timeout in seconds
        
    def add_document(self, file_path: str):
        self.queue.put(file_path)
        
    def process_queue(self, processor: Callable) -> Dict[str, Any]:
        """Process documents in parallel using worker threads."""
        start_time = time.time()
        total_files = self.queue.qsize()
        processed = 0
        
        def worker():
            while True:
                if time.time() - start_time > self.timeout:
                    logger.warning("Processing timeout reached")
                    break
                    
                try:
                    file_path = self.queue.get_nowait()
                except Empty:
                    break
                    
                try:
                    logger.info(f"Processing file: {file_path}")
                    result = processor(file_path)
                    self.results[file_path] = {
                        'status': 'success',
                        'result': result,
                        'timestamp': time.time()
                    }
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
                    self.results[file_path] = {
                        'status': 'error',
                        'error': str(e),
                        'timestamp': time.time()
                    }
                finally:
                    self.queue.task_done()
                    nonlocal processed
                    processed += 1
                    logger.info(f"Progress: {processed}/{total_files} files processed")
        
        threads = []
        for _ in range(min(self.num_workers, total_files)):
            t = Thread(target=worker)
            t.daemon = True  # Make threads daemon so they exit when main thread exits
            t.start()
            threads.append(t)
            
        # Wait for all threads with timeout
        for t in threads:
            t.join(timeout=self.timeout)
            
        # Check if all files were processed
        remaining = self.queue.qsize()
        if remaining > 0:
            logger.warning(f"{remaining} files were not processed due to timeout")
            
        return {
            'results': self.results,
            'total_files': total_files,
            'processed_files': processed,
            'failed_files': sum(1 for r in self.results.values() if r['status'] == 'error'),
            'processing_time': time.time() - start_time
        }

def main():
    # Initialize components
    parser = DocumentParser()
    queue = DocumentProcessingQueue(num_workers=3, timeout=300)
    
    # Add documents to queue
    documents = [
        # "path/to/doc1.pdf",
        # "path/to/doc2.docx",
        # "path/to/doc3.md"
        "test.pdf"
    ]
    
    for doc in documents:
        if os.path.exists(doc):  # Only add existing files
            queue.add_document(doc)
        else:
            logger.warning(f"File not found: {doc}")
    
    # Process documents
    results = queue.process_queue(parser.parse_file)
    
    # Print summary
    print("\nProcessing Summary:")
    print(f"Total files: {results['total_files']}")
    print(f"Processed files: {results['processed_files']}")
    print(f"Failed files: {results['failed_files']}")
    print(f"Processing time: {results['processing_time']:.2f} seconds")
    
    # Print detailed results
    print("\nDetailed Results:")
    for file_path, result in results['results'].items():
        status = result['status']
        if status == 'success':
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}: {result['error']}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nScript failed with error: {str(e)}")
        sys.exit(1)
