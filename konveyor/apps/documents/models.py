from django.db import models
import uuid
import os
from django.core.exceptions import ValidationError

def validate_file_extension(value):
    valid_extensions = ['.pdf', '.docx', '.md', '.txt']
    ext = os.path.splitext(value.name)[1]
    if ext.lower() not in valid_extensions:
        raise ValidationError('Unsupported file type.')

class Document(models.Model):
    """Model for tracking documents."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    blob_path = models.CharField(max_length=512)  # Path in Azure Blob Storage
    content_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PROCESSING', 'Processing'),
            ('PROCESSED', 'Processed'),
            ('FAILED', 'Failed')
        ],
        default='PENDING'
    )
    error_message = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    
    def __str__(self):
        return self.title

class DocumentChunk(models.Model):
    """Model for tracking document chunks."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    blob_path = models.CharField(max_length=512)  # Path in Azure Blob Storage
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['document', 'chunk_index']
