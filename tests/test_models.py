from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from konveyor.apps.documents.models import Document

class DocumentModelTests(TestCase):
    def test_document_creation(self):
        test_file = SimpleUploadedFile(
            "test.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        doc = Document.objects.create(
            title="Test Document",
            file=test_file
        )
        self.assertEqual(doc.title, "Test Document")
