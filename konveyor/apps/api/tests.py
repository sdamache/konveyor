import json

from django.test import Client, TestCase
from django.urls import reverse


class ApiViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_azure_openai_status_view(self):
        """Test the Azure OpenAI status endpoint"""
        response = self.client.get(reverse("api:azure_openai_status"))
        self.assertEqual(response.status_code, 200)

        # Parse JSON response
        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["integration"], "Azure OpenAI")
