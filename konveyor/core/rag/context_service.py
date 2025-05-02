"""
Context service for RAG operations.
Integrates Azure Document Intelligence, AI Search, and OpenAI for document processing and retrieval.  # noqa: E501
"""

import os
from typing import Dict, List, Optional, Tuple  # noqa: F401

from openai import AzureOpenAI

from konveyor.core.azure_utils.clients import AzureClientManager


class ContextService:
    """Service for document processing and context retrieval using Azure services."""

    def __init__(self, client_manager: AzureClientManager):
        self.client_manager = client_manager
        _, self.search_client = self.client_manager.get_search_clients(
            "konveyor-documents"
        )
        self.openai_client = self.client_manager.get_openai_client()
        self.doc_client = self.client_manager.get_document_intelligence_client()

    async def process_document(self, content: bytes, filename: str) -> List[Dict]:
        """Process a document using Azure Document Intelligence and prepare for indexing."""  # noqa: E501
        # Extract text using Document Intelligence
        result = await self.doc_client.analyze_document(content)

        # Chunk the content (simplified - you might want more sophisticated chunking)
        chunks = self._chunk_content(result.content, chunk_size=1000)

        # Generate embeddings for chunks
        chunk_documents = []
        for i, (chunk_text, page_num) in enumerate(chunks):
            embedding = await self.openai_client.embeddings.create(
                model=self.client_manager.config.openai_embedding_deployment,
                input=chunk_text,
            )

            chunk_documents.append(
                {
                    "id": f"{filename}-chunk-{i}",
                    "content": chunk_text,
                    "content_vector": embedding.data[0].embedding,
                    "source": filename,
                    "page_number": page_num,
                    "metadata": {
                        "file_type": filename.split(".")[-1],
                        "chunk_index": i,
                    },
                }
            )

        # Index chunks in Azure AI Search
        await self.search_client.upload_documents(chunk_documents)
        return chunk_documents

    def _chunk_content(self, content: str, chunk_size: int) -> List[Tuple[str, int]]:
        """Split content into chunks while preserving page boundaries."""
        # Simplified chunking - you might want more sophisticated logic
        chunks = []
        current_chunk = ""
        current_page = 1

        for line in content.split("\n"):
            if len(current_chunk) + len(line) > chunk_size:
                chunks.append((current_chunk.strip(), current_page))
                current_chunk = line
            else:
                current_chunk += "\n" + line

            # Simple page detection - enhance based on your needs
            if "[Page Break]" in line:  # Adjust based on actual page break marker
                current_page += 1

        if current_chunk:
            chunks.append((current_chunk.strip(), current_page))

        return chunks

    async def retrieve_context(
        self, query: str, max_chunks: int = 3, min_relevance_score: float = 0.3
    ) -> List[Dict[str, any]]:
        """Retrieve relevant context using hybrid search in Azure AI Search."""
        # Generate query embedding
        # Create embeddings client
        embedding_deployment = os.environ.get(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "embeddings"
        )
        embedding_client = AzureOpenAI(
            azure_endpoint=self.client_manager.config.get_endpoint("OPENAI"),
            api_key=self.client_manager.config.get_key("OPENAI"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
            azure_deployment=embedding_deployment,
        )

        # Generate embedding
        query_embedding = embedding_client.embeddings.create(
            model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "embeddings"),
            input=query,
        )

        # Perform hybrid search (combines keyword and vector search)
        search_results = self.search_client.search(
            search_text=query,  # For keyword search
            select=[
                "id",
                "content",
                "document_id",
                "chunk_id",
                "chunk_index",
                "metadata",
            ],  # Fields to retrieve
            top=max_chunks,
            vector_queries=[
                {
                    "vector": query_embedding.data[0].embedding,
                    "fields": "embedding",  # Match the field name from index
                    "k": max_chunks,
                    "kind": "vector",
                }
            ],
        )

        # Process and filter results
        context_chunks = []
        for result in search_results:
            if result.get("@search.score", 0) < min_relevance_score:
                continue

            context_chunks.append(
                {
                    "content": result["content"],
                    "source": f"Document {result['document_id']}, Chunk {result['chunk_id']}",  # noqa: E501
                    "page": result.get("chunk_index"),
                    "relevance_score": result["@search.score"],
                    "metadata": result.get("metadata", {}),
                }
            )

        return context_chunks

    def format_context(self, chunks: List[Dict[str, any]]) -> str:
        """Format retrieved chunks with source citations and metadata."""
        if not chunks:
            return "No relevant context found."

        formatted_chunks = []
        for chunk in chunks:
            # Build detailed source citation
            source_citation = f"[Source: {chunk['source']}"
            if chunk.get("page"):
                source_citation += f", Page {chunk['page']}"
            if chunk.get("metadata", {}).get("file_type"):
                source_citation += f", Type: {chunk['metadata']['file_type']}"
            source_citation += f", Relevance: {chunk['relevance_score']:.2f}]"

            formatted_chunks.append(f"{chunk['content']}\n{source_citation}\n")

        return "\n\n".join(formatted_chunks)
