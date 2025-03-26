import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
)
from django.conf import settings

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        self.endpoint = settings.AZURE_COGNITIVE_SEARCH_ENDPOINT
        self.api_key = settings.AZURE_SEARCH_API_KEY
        self.index_name = settings.AZURE_SEARCH_INDEX_NAME
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Search endpoint and API key must be configured")
            
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )
    
    def create_search_index(self) -> SearchIndex:
        """Create the search index."""
        fields = [
            SimpleField(
                name="id", 
                type=SearchFieldDataType.String, 
                key=True,
                searchable=False
            ),
            SimpleField(
                name="document_id", 
                type=SearchFieldDataType.String, 
                filterable=True
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                analyzer_name="standard.lucene"
            ),
            SimpleField(
                name="chunk_index", 
                type=SearchFieldDataType.Int32,
                filterable=True,
                sortable=True
            ),
            SimpleField(
                name="metadata", 
                type=SearchFieldDataType.String,
                filterable=True
            ),
            SimpleField(
                name="created_at",
                type=SearchFieldDataType.DateTimeOffset,
                filterable=True,
                sortable=True
            ),
            SimpleField(
                name="file_type",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            )
        ]
        
        index = SearchIndex(
            name=self.index_name,
            fields=fields
        )
        
        return self.index_client.create_or_update_index(index)

    def delete_index(self) -> None:
        """Delete the search index if it exists."""
        try:
            self.index_client.delete_index(self.index_name)
            logger.info(f"Search index '{self.index_name}' deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete search index: {str(e)}")
            raise
    
    def get_index(self) -> SearchIndex:
        """Get the current search index configuration."""
        try:
            return self.index_client.get_index(self.index_name)
        except Exception as e:
            logger.error(f"Failed to get search index '{self.index_name}': {str(e)}")
            raise 