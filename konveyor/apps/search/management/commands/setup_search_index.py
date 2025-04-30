from django.core.management.base import BaseCommand
from django.conf import settings
from ...services.search_service import SearchService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sets up the Azure Cognitive Search index for documents"

    def handle(self, *args, **options):
        try:
            # Initialize search service
            search_service = SearchService()

            # List existing indexes
            self.stdout.write("Checking existing indexes...")
            indexes = list(search_service.index_client.list_indexes())
            index_names = [idx.name for idx in indexes]

            if settings.AZURE_SEARCH_INDEX_NAME in index_names:
                self.stdout.write(
                    f"Index '{settings.AZURE_SEARCH_INDEX_NAME}' already exists"
                )
                return

            # Create the index
            self.stdout.write("Creating search index...")
            success = search_service.create_search_index()
            if success:
                self.stdout.write(
                    f"Successfully created index '{search_service.index_name}'"
                )
            else:
                self.stdout.write("Failed to create search index")

        except Exception as e:
            self.stdout.write(f"Error: {str(e)}")
            raise
