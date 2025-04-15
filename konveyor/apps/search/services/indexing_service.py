"""Document indexing service for Azure Cognitive Search.

This module provides functionality for indexing documents in Azure Cognitive Search,
including batch processing and optimization.

Example:
    ```python
    # Initialize service
    indexing = IndexingService()
    
    # Index a document
    document = Document.objects.get(id=1)
    indexing.index_document(document)
    ```
"""

from typing import Dict, Any, List
from django.db import transaction
import logging
import time

from konveyor.apps.documents.models import Document, DocumentChunk
from konveyor.core.documents.document_service import DocumentService
from konveyor.apps.search.services.search_service import SearchService
from konveyor.core.azure_utils.service import AzureService

class IndexingService(AzureService):
    """Service for indexing documents in Azure Cognitive Search.
    
    This service provides methods for:
    - Indexing documents and their chunks
    - Batch processing with size optimization
    - Progress tracking and error handling
    
    Attributes:
        search_service (SearchService): Service for search operations
        document_service (DocumentService): Service for document processing
        min_batch_size (int): Minimum batch size for indexing
        max_batch_size (int): Maximum batch size (Azure limit)
        max_batch_size_bytes (int): Maximum batch size in bytes (Azure limit)
    """
    
    def __init__(self):
        """Initialize indexing service.
        
        Sets up search and document services, and configures batch size limits.
        
        Raises:
            Exception: If service initialization fails
        """
        # Initialize base class
        super().__init__('SEARCH')
        self.log_init("IndexingService")
        
        try:
            # Initialize services
            self.search_service = SearchService()
            self.document_service = DocumentService()
            
            # Configure batch sizing
            self.min_batch_size = 10
            self.max_batch_size = 1000  # Azure Search limit
            self.max_batch_size_bytes = 16 * 1024 * 1024  # 16 MB Azure Search limit
            
            self.log_success("Initialized with adaptive batch sizing")
            
        except Exception as e:
            self.log_error("Failed to initialize service", e)
            raise
    
    def _calculate_batch_size(self, chunks: List[DocumentChunk]) -> int:
        """Calculate optimal batch size based on content size.
        
        Uses a sampling approach to estimate average chunk size and determine
        the optimal batch size that stays within Azure limits.
        
        Args:
            chunks (List[DocumentChunk]): List of chunks to analyze
            
        Returns:
            int: Optimal batch size between min_batch_size and max_batch_size
        """
        if not chunks:
            self.log_debug("No chunks provided, using minimum batch size")
            return self.min_batch_size
            
        # Sample first few chunks to estimate average size
        sample_size = min(10, len(chunks))
        self.log_debug(f"Sampling {sample_size} chunks for size estimation")
        total_bytes = sum(len(chunk.content.encode('utf-8')) for chunk in chunks[:sample_size])
        avg_bytes_per_chunk = total_bytes / sample_size
        
        # Calculate batch size based on size limits
        size_based_limit = int(self.max_batch_size_bytes / avg_bytes_per_chunk)
        return min(size_based_limit, self.max_batch_size, max(self.min_batch_size, len(chunks)))
    
    @transaction.atomic
    def index_document(self, document_id: str) -> Dict[str, Any]:
        """
        Index all chunks of a document with improved batch processing and error handling.
        """
        try:
            logger.info("Starting indexing for document_id=%s", document_id)
            
            # Get the document and its chunks
            document = Document.objects.get(id=document_id)
            chunks = DocumentChunk.objects.filter(document=document).order_by('chunk_index')
            total_chunks = chunks.count()
            
            if not total_chunks:
                raise ValueError(f"No chunks found for document {document_id}")
            
            logger.info(
                "Found document '%s' with %d chunks to process",
                document.title if hasattr(document, 'title') else document_id,
                total_chunks
            )
            
            # Ensure search index exists with latest configuration
            self.search_service.create_search_index()
            logger.debug("Verified search index exists")
            
            # Initialize results tracking
            results = {
                "document_id": str(document_id),
                "total_chunks": total_chunks,
                "indexed_chunks": 0,
                "failed_chunks": 0,
                "failed_chunk_ids": [],
                "retried_chunks": 0,
                "processing_time": 0,
                "batch_stats": []
            }
            
            start_time = time.time()
            
            # Process chunks with adaptive batch sizing
            chunk_list = list(chunks)
            while chunk_list:
                batch_size = self._calculate_batch_size(chunk_list)
                batch = chunk_list[:batch_size]
                chunk_list = chunk_list[batch_size:]
                
                batch_num = len(results["batch_stats"]) + 1
                total_batches = (total_chunks + batch_size - 1) // batch_size
                
                logger.info(
                    "Processing batch %d/%d for document %s (%d chunks)",
                    batch_num, total_batches, document_id, len(batch)
                )
                
                batch_results = self._index_chunk_batch(batch)
                
                # Update results with batch statistics
                results["indexed_chunks"] += batch_results["success"]
                results["failed_chunks"] += batch_results["failed"]
                results["failed_chunk_ids"].extend(batch_results["failed_ids"])
                results["retried_chunks"] += batch_results.get("retries", 0)
                results["batch_stats"].append({
                    "batch_number": batch_num,
                    "batch_size": len(batch),
                    "successful": batch_results["success"],
                    "failed": batch_results["failed"],
                    "retries": batch_results.get("retries", 0)
                })
                
                logger.info(
                    "Batch %d/%d completed. Success: %d, Failed: %d, Retries: %d",
                    batch_num, total_batches, 
                    batch_results["success"], 
                    batch_results["failed"],
                    batch_results.get("retries", 0)
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
        Index a batch of document chunks with improved error handling and retries.
        """
        results = {"success": 0, "failed": 0, "failed_ids": [], "retries": 0}
        
        for chunk in chunks:
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    logger.debug(
                        "Processing chunk %s (index: %d) from document %s",
                        chunk.id, chunk.chunk_index, chunk.document.id
                    )
                    
                    # Get chunk content from blob storage
                    content = self.document_service.get_chunk_content(chunk)
                    
                    # Generate embedding with retry logic
                    embedding = self.search_service.generate_embedding(content)
                    logger.debug("Generated embedding for chunk %s", chunk.id)
                    
                    # Index the chunk with vector search support
                    self.search_service.index_document_chunk(
                        chunk_id=str(chunk.id),
                        document_id=str(chunk.document.id),
                        content=content,
                        chunk_index=chunk.chunk_index,
                        metadata=chunk.metadata,
                        embedding=embedding
                    )
                    
                    results["success"] += 1
                    if retry_count > 0:
                        results["retries"] += retry_count
                    logger.debug("Successfully indexed chunk %s", chunk.id)
                    break
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.warning(
                            "Retry %d/%d for chunk %s after error: %s",
                            retry_count, max_retries, chunk.id, str(e)
                        )
                        time.sleep(2 ** retry_count)  # Exponential backoff
                    else:
                        logger.error(
                            "Failed to index chunk %s after %d retries: %s",
                            chunk.id, max_retries, str(e), exc_info=True
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