"""Document chunk processing service.

This module provides functionality for processing and managing document chunks,
including size optimization and batch processing.

Example:
    ```python
    # Initialize service
    chunk_service = ChunkService()

    # Process chunks with optimal batch size
    chunks = [...]  # List of document chunks
    batch_size = chunk_service.calculate_batch_size(chunks)
    for batch in chunk_service.process_in_batches(chunks, batch_size):
        # Process batch
        pass
    ```
"""

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from konveyor.core.azure_utils.service import AzureService

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of a document.

    Attributes:
        id (str): Unique identifier for the chunk
        document_id (str): ID of the parent document
        content (str): Text content of the chunk
        chunk_index (int): Index of this chunk in the document
        metadata (Dict[str, Any]): Additional metadata about the chunk
    """

    id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: dict[str, Any]


class ChunkService(AzureService):
    """Service for processing document chunks.

    This service provides methods for optimizing and processing document chunks,
    including batch size calculation and efficient batch processing.

    Attributes:
        max_chunk_size (int): Maximum size of a single chunk in characters
        max_batch_size (int): Maximum number of chunks in a batch
    """

    def __init__(self, max_chunk_size: int = 5000, max_batch_size: int = 100):
        """Initialize chunk service.

        Args:
            max_chunk_size (int, optional): Maximum size of a chunk. Defaults to 5000.
            max_batch_size (int, optional): Maximum batch size. Defaults to 100.
        """
        super().__init__("DOCUMENT_INTELLIGENCE")
        self.log_init("ChunkService")

        self.max_chunk_size = max_chunk_size
        self.max_batch_size = max_batch_size
        self.log_success(
            f"Initialized with max_chunk_size={max_chunk_size}, max_batch_size={max_batch_size}"  # noqa: E501
        )

    def calculate_batch_size(self, chunks: list[DocumentChunk]) -> int:
        """Calculate optimal batch size based on chunk contents.

        This method analyzes the chunks to determine the optimal batch size
        that balances processing efficiency with memory usage.

        Args:
            chunks (List[DocumentChunk]): List of document chunks to analyze

        Returns:
            int: Optimal batch size, will not exceed max_batch_size
        """
        if not chunks:
            return self.max_batch_size

        # Calculate average chunk size
        total_size = sum(len(chunk.content) for chunk in chunks)
        avg_size = total_size / len(chunks)

        # Adjust batch size based on average chunk size
        if avg_size > self.max_chunk_size:
            optimal_size = max(1, self.max_batch_size // 2)
        else:
            # Scale batch size inversely with chunk size
            size_ratio = self.max_chunk_size / avg_size
            optimal_size = min(
                self.max_batch_size, int(self.max_batch_size * (size_ratio / 10))
            )

        self.log_debug(
            f"Calculated optimal batch size: {optimal_size} for avg chunk size: {avg_size:.0f}"  # noqa: E501
        )
        return optimal_size

    def process_in_batches(
        self, chunks: list[DocumentChunk], batch_size: int | None = None
    ) -> Iterator[list[DocumentChunk]]:
        """Process chunks in optimally sized batches.

        Args:
            chunks (List[DocumentChunk]): List of chunks to process
            batch_size (Optional[int]): Override calculated batch size

        Yields:
            Iterator[List[DocumentChunk]]: Batches of chunks

        Example:
            ```python
            chunks = [...]  # List of document chunks
            for batch in service.process_in_batches(chunks):
                process_batch(batch)
            ```
        """
        if not chunks:
            self.log_warning("No chunks to process")
            return

        # Use provided batch size or calculate optimal
        actual_batch_size = batch_size or self.calculate_batch_size(chunks)
        total_chunks = len(chunks)

        self.log_debug(
            f"Processing {total_chunks} chunks in batches of {actual_batch_size}"
        )

        # Yield batches
        for i in range(0, total_chunks, actual_batch_size):
            batch = chunks[i : i + actual_batch_size]
            self.log_debug(
                f"Processing batch {i // actual_batch_size + 1} with {len(batch)} chunks"
            )
            yield batch

    def validate_chunk(self, chunk: DocumentChunk) -> bool:
        """Validate a document chunk.

        Checks that the chunk has all required fields and valid content.

        Args:
            chunk (DocumentChunk): Chunk to validate

        Returns:
            bool: True if chunk is valid, False otherwise

        Example:
            ```python
            chunk = DocumentChunk(...)
            if service.validate_chunk(chunk):
                process_chunk(chunk)
            ```
        """
        try:
            # Check required fields
            if not all([chunk.id, chunk.document_id, chunk.content]):
                self.log_warning(f"Chunk {chunk.id} missing required fields")
                return False

            # Validate content size
            if len(chunk.content) > self.max_chunk_size:
                self.log_warning(
                    f"Chunk {chunk.id} exceeds max size: {len(chunk.content)} > {self.max_chunk_size}"  # noqa: E501
                )
                return False

            # Validate metadata
            if not isinstance(chunk.metadata, dict):
                self.log_warning(
                    f"Chunk {chunk.id} has invalid metadata type: {type(chunk.metadata)}"  # noqa: E501
                )
                return False

            return True

        except Exception as e:
            self.log_error(f"Error validating chunk {chunk.id}", e)
            return False
