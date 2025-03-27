from typing import Dict, Any, List
from django.db import transaction
import logging
from documents.models import Document, DocumentChunk
from documents.services.document_service import DocumentService
from .search_service import SearchService

# Configure logger
logger = logging.getLogger(__name__)

class IndexingService:
    """Service for indexing documents in the search service."""
    
    def __init__(self):
        self.search_service = SearchService()
        self.document_service = DocumentService()
        self.batch_size = 10  # Adjust based on your needs
        logger.info("Initialized IndexingService with batch_size=%d", self.batch_size)
    
    @transaction.atomic
    def index_document(self, document_id: str) -> Dict[str, Any]:
        """
        Index all chunks of a document.
        
        Args:
            document_id: The ID of the document to index
            
        Returns:
            Dictionary with indexing results
        """
        try:
            logger.info("Starting indexing for document_id=%s", document_id)
            
            # Get the document and its chunks
            document = Document.objects.get(id=document_id)
            chunks = DocumentChunk.objects.filter(document=document).order_by('chunk_index')
            total_chunks = chunks.count()
            
            logger.info(
                "Found document '%s' with %d chunks to process",
                document.title if hasattr(document, 'title') else document_id,
                total_chunks
            )
            
            # Ensure search index exists
            self.search_service.create_search_index()
            logger.debug("Verified search index exists")
            
            # Process chunks in batches
            results = {
                "document_id": str(document_id),
                "total_chunks": total_chunks,
                "indexed_chunks": 0,
                "failed_chunks": 0,
                "failed_chunk_ids": [],
                "processing_time": 0
            }
            
            # Process chunks in batches
            import time
            start_time = time.time()
            
            for i in range(0, total_chunks, self.batch_size):
                batch = chunks[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (total_chunks + self.batch_size - 1) // self.batch_size
                
                logger.info(
                    "Processing batch %d/%d for document %s (%d chunks)",
                    batch_num, total_batches, document_id, len(batch)
                )
                
                batch_results = self._index_chunk_batch(batch)
                
                results["indexed_chunks"] += batch_results["success"]
                results["failed_chunks"] += batch_results["failed"]
                results["failed_chunk_ids"].extend(batch_results["failed_ids"])
                
                logger.info(
                    "Batch %d/%d completed. Success: %d, Failed: %d",
                    batch_num, total_batches, batch_results["success"], batch_results["failed"]
                )
            
            end_time = time.time()
            processing_time = end_time - start_time
            results["processing_time"] = round(processing_time, 2)
            
            success_rate = (results["indexed_chunks"] / total_chunks) * 100 if total_chunks > 0 else 0
            
            logger.info(
                "Completed indexing document %s. Success rate: %.2f%% (%d/%d chunks) in %.2f seconds",
                document_id, success_rate, results["indexed_chunks"], total_chunks, processing_time
            )
            
            if results["failed_chunks"] > 0:
                logger.warning(
                    "Failed to index %d chunks in document %s: %s",
                    results["failed_chunks"], document_id, results["failed_chunk_ids"]
                )
            
            return results
            
        except Document.DoesNotExist:
            error_msg = f"Document {document_id} not found"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error indexing document {document_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise
    
    def _index_chunk_batch(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """
        Index a batch of document chunks.
        
        Args:
            chunks: List of DocumentChunk instances
            
        Returns:
            Dictionary with batch indexing results
        """
        results = {"success": 0, "failed": 0, "failed_ids": []}
        
        for chunk in chunks:
            try:
                logger.debug(
                    "Processing chunk %s (index: %d) from document %s",
                    chunk.id, chunk.chunk_index, chunk.document.id
                )
                
                # Get chunk content from blob storage
                content = self.document_service.get_chunk_content(chunk)
                
                # Generate embedding
                embedding = self.search_service.generate_embedding(content)
                logger.debug("Generated embedding for chunk %s", chunk.id)
                
                # Index the chunk
                self.search_service.index_document_chunk(
                    chunk_id=str(chunk.id),
                    document_id=str(chunk.document.id),
                    content=content,
                    chunk_index=chunk.chunk_index,
                    metadata=chunk.metadata,
                    embedding=embedding
                )
                
                results["success"] += 1
                logger.debug("Successfully indexed chunk %s", chunk.id)
                
            except Exception as e:
                logger.error(
                    "Failed to index chunk %s: %s",
                    chunk.id, str(e), exc_info=True
                )
                results["failed"] += 1
                results["failed_ids"].append(str(chunk.id))
        
        return results
    
    def index_all_documents(self) -> List[Dict[str, Any]]:
        """
        Index all documents in the database.
        
        Returns:
            List of indexing results for each document
        """
        logger.info("Starting bulk indexing of all documents")
        results = []
        documents = Document.objects.all()
        total_documents = documents.count()
        
        logger.info("Found %d documents to index", total_documents)
        
        for i, document in enumerate(documents, 1):
            try:
                logger.info(
                    "Processing document %d/%d (ID: %s)",
                    i, total_documents, document.id
                )
                result = self.index_document(str(document.id))
                results.append(result)
            except Exception as e:
                error_result = {
                    "document_id": str(document.id),
                    "error": str(e)
                }
                results.append(error_result)
                logger.error(
                    "Failed to index document %s: %s",
                    document.id, str(e), exc_info=True
                )
        
        successful_docs = len([r for r in results if "error" not in r])
        logger.info(
            "Bulk indexing completed. Successfully processed %d/%d documents",
            successful_docs, total_documents
        )
        
        return results 