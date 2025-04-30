from django.test import TestCase, Client
from django.urls import reverse
import json


class CoreViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index_view(self):
        """Test the index view returns the expected JSON response"""
        response = self.client.get(reverse("core:index"))
        self.assertEqual(response.status_code, 200)

        # Parse JSON response
        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["message"], "Konveyor API is running")
