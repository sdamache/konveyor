from django.db import models
import uuid


class SearchDocument(models.Model):
    """
    Model to track document metadata and search status.
    The actual content is stored in Azure Blob Storage.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document_id = models.UUIDField()  # Reference to original document
    blob_path = models.CharField(max_length=512)  # Path in Azure Blob Storage
    indexed_at = models.DateTimeField(null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("INDEXING", "Indexing"),
            ("INDEXED", "Indexed"),
            ("FAILED", "Failed"),
        ],
        default="PENDING",
    )
    error_message = models.TextField(null=True, blank=True)
    chunk_count = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=["document_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["indexed_at"]),
        ]
