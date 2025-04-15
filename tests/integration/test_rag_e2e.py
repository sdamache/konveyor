import os
import pytest
import pytest_asyncio
from pathlib import Path

# Set Django settings module before importing any Django code
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'konveyor.settings.development')

# Import Django settings and setup
from django.conf import settings
import django
django.setup()

# Import settings loader first
from konveyor.settings.settings_loader import load_settings

# Load environment settings
load_settings()

# Now import the rest
from konveyor.core.rag.rag_service import RAGService
from konveyor.core.rag.context_service import ContextService
from konveyor.core.azure_utils.storage import AzureStorageManager
from konveyor.core.azure_utils.clients import AzureClientManager
from konveyor.apps.search.services.indexing_service import IndexingService
from konveyor.apps.search.services.search_service import SearchService
from konveyor.apps.documents.services.document_service import DocumentService

@pytest.mark.integration
class TestRAGIntegration:
    """End-to-end tests for RAG functionality using real Azure services"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self):
        """Setup test environment with real Azure services"""
        # Initialize services with real Azure clients
        client_manager = AzureClientManager()
        
        # Initialize storage manager
        self.storage_manager = client_manager.get_storage_manager()
        await self.storage_manager.initialize()
        
        # Initialize services
        self.rag_service = RAGService(client_manager)
        self.indexing_service = IndexingService()
        self.search_service = SearchService()
        self.document_service = DocumentService()
        
        # Index test documents
        test_docs = {
            "kubernetes_pods.md": "A Pod is the smallest deployable unit in Kubernetes. It represents a single instance of a running process in your cluster. A Pod can contain one or more containers that share storage and network resources. Pods are typically managed by higher-level controllers like Deployments.",
            "kubernetes_deployments.md": "A Deployment in Kubernetes provides declarative updates for Pods and ReplicaSets. You describe a desired state in a Deployment, and the Deployment Controller changes the actual state to the desired state at a controlled rate. Deployments are perfect for stateless applications.",
            "kubernetes_services.md": "A Kubernetes Service is an abstraction layer that defines a logical set of Pods and enables external traffic exposure, load balancing and service discovery for those Pods. Services enable loose coupling between dependent Pods and can span multiple deployments."
        }
        
        # Process and index each document
        for filename, content in test_docs.items():
            # Store document
            doc = await self.document_service.store_document(
                content.encode(),
                filename,
                "text/markdown",
                title=filename
            )
            
            # Index document for search
            await self.indexing_service.index_document(doc.id)
        
        # Create a test conversation
        self.conversation = await self.storage_manager.create_conversation()
        yield
        # Cleanup
        await self.storage_manager.delete_conversation(self.conversation["id"])
        self.storage_manager.mongo_client.close()
        await self.storage_manager.redis_client.aclose()

    @pytest.mark.asyncio
    async def test_kubernetes_basic_concepts(self):
        """Test RAG with basic Kubernetes concepts"""
        queries = [
            "What is a Kubernetes Pod?",
            "How do Deployments work in Kubernetes?",
            "Explain Kubernetes Services"
        ]
        
        for query in queries:
            response = await self.rag_service.generate_response(
                query, 
                conversation_id=self.conversation["id"]
            )
            
            # Verify response quality
            assert len(response["answer"]) > 100
            assert len(response["sources"]) >= 1
            assert all("kubernetes" in s["source"].lower() for s in response["sources"])
            
            # Verify conversation storage
            messages = await self.storage_manager.get_conversation_messages(
                self.conversation["id"]
            )
            assert len(messages) > 0
            assert any(m["content"] == query for m in messages)

    @pytest.mark.asyncio
    async def test_linux_kernel_concepts(self):
        """Test RAG with Linux kernel concepts"""
        queries = [
            "How do Linux system calls work?",
            "Explain Linux process scheduling",
            "What are Linux kernel modules?"
        ]
        
        for query in queries:
            response = await self.rag_service.generate_response(
                query,
                conversation_id=self.conversation["id"]
            )
            
            assert len(response["answer"]) > 100
            assert len(response["sources"]) >= 1
            assert all("linux" in s["source"].lower() for s in response["sources"])

    @pytest.mark.asyncio
    async def test_container_runtime_interaction(self):
        """Test RAG with questions about container runtime and kernel interaction"""
        query = "How do Kubernetes containers interact with the Linux kernel?"
        
        response = await self.rag_service.generate_response(
            query,
            conversation_id=self.conversation["id"]
        )
        
        # Verify cross-domain knowledge
        assert len(response["answer"]) > 100
        assert any("kubernetes" in s["source"].lower() for s in response["sources"])
        assert any("linux" in s["source"].lower() for s in response["sources"])
        assert "container" in response["answer"].lower()
        assert "kernel" in response["answer"].lower()

    @pytest.mark.asyncio
    async def test_code_example_generation(self):
        """Test RAG's ability to provide code examples"""
        queries = [
            "Show me a Kubernetes Pod YAML example",
            "How to write a simple Linux kernel module?",
            "Example of a Kubernetes Deployment with multiple replicas"
        ]
        
        for query in queries:
            response = await self.rag_service.generate_response(
                query,
                template_type="code",
                conversation_id=self.conversation["id"]
            )
            
            assert "```" in response["answer"]  # Contains code blocks
            assert len(response["sources"]) >= 1
            
            if "kubernetes" in query.lower():
                assert "apiVersion" in response["answer"]
                assert "kind:" in response["answer"]
            if "linux" in query.lower():
                assert "#include" in response["answer"]

    @pytest.mark.asyncio
    async def test_conversation_context(self):
        """Test RAG's ability to maintain context in a conversation"""
        queries = [
            "What is a Kubernetes Pod?",
            "How is it different from a container?",
            "Can you show me an example?",
            "How does it interact with the Linux kernel?"
        ]
        
        for query in queries:
            response = await self.rag_service.generate_response(
                query,
                conversation_id=self.conversation["id"]
            )
            
            assert len(response["answer"]) > 50
            assert len(response["sources"]) >= 1
            
            # Verify conversation storage and context
            messages = await self.storage_manager.get_conversation_messages(
                self.conversation["id"]
            )
            assert len(messages) > 0
            assert messages[-1]["content"] == query
