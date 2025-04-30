from django.conf import settings

DOCUMENT_SETTINGS = {
    "MAX_FILE_SIZE": getattr(settings, "MAX_DOCUMENT_FILE_SIZE", 10 * 1024 * 1024),
    "ALLOWED_EXTENSIONS": getattr(
        settings, "ALLOWED_DOCUMENT_EXTENSIONS", [".pdf", ".docx", ".md", ".txt"]
    ),
    "CHUNK_SIZE": getattr(settings, "DOCUMENT_CHUNK_SIZE", 1000),
    "CHUNK_OVERLAP": getattr(settings, "DOCUMENT_CHUNK_OVERLAP", 200),
}
