import logging

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import status, views
from rest_framework.response import Response

from .models import SearchQuery, SearchResult
from .services.indexing_service import IndexingService
from .services.search_service import SearchService

# Configure logger
logger = logging.getLogger(__name__)


# Convert SearchViewSet to use APIView format
class QuerySearchView(views.APIView):
    """Search API endpoint for semantic document search."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_service = SearchService()

    def post(self, request, format=None):
        """
        Search for documents using a text query.
        """
        query_text = request.data.get("query")
        top = request.data.get("top", 5)

        if not query_text:
            return Response(
                {"error": "Query text is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Save the search query
            search_query = SearchQuery.objects.create(
                query_text=query_text,
                user=request.user if request.user.is_authenticated else None,
            )

            # Perform the search
            results = self.search_service.semantic_search(query_text, top=top)

            # Save the search results
            for i, result in enumerate(results):
                SearchResult.objects.create(
                    search_query=search_query,
                    document_id=result["document_id"],
                    chunk_id=result["id"],
                    relevance_score=result["score"],
                    position=i,
                )

            return Response({"query_id": str(search_query.id), "results": results})
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentIndexView(views.APIView):
    """API endpoint for document indexing operations."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.indexing_service = IndexingService()

    def post(self, request, format=None):
        """
        Index a document in the search service.
        """
        document_id = request.data.get("document_id")

        if not document_id:
            return Response(
                {"error": "Document ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = self.indexing_service.index_document(document_id)
            return Response(
                {"status": "Document indexed successfully", "details": result}
            )
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReindexAllView(views.APIView):
    """API endpoint for reindexing all documents."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.indexing_service = IndexingService()

    def post(self, request, format=None):
        """
        Reindex all documents in the database.
        """
        try:
            results = self.indexing_service.index_all_documents()
            return Response(
                {"status": "All documents indexed successfully", "results": results}
            )
        except Exception as e:
            logger.error(f"Error reindexing all documents: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SimpleSearchView(views.APIView):
    """Simple search endpoint supporting GET and POST methods."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_service = SearchService()

    def get(self, request, format=None):
        """Handle GET search requests with query parameters."""
        query = request.query_params.get("q")
        top = int(request.query_params.get("top", 5))

        if not query:
            return Response(
                {"error": "Query parameter 'q' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            results = self.search_service.semantic_search(query, top=top)

            return Response({"query": query, "results": results})
        except Exception as e:
            logger.error(f"Error in GET search: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, format=None):
        """Handle POST search requests with JSON body."""
        query = request.data.get("query")
        top = request.data.get("top", 5)

        if not query:
            return Response(
                {"error": "Query parameter 'query' is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            results = self.search_service.semantic_search(query, top=top)

            return Response({"query": query, "results": results})
        except Exception as e:
            logger.error(f"Error in POST search: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
