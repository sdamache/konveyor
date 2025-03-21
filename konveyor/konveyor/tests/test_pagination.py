from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from konveyor.apps.api.models import ExampleModel

class PaginationTests(APITestCase):
    def setUp(self):
        for i in range(15):
            ExampleModel.objects.create(name=f'Test Model {i}', description='Test Description')

    def test_pagination_default_page_size(self):
        # Must have
        url = reverse('examplemodel-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_pagination_custom_page_size(self):
        # Must have
        url = reverse('examplemodel-list') + '?page_size=5'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

    def test_pagination_next_page(self):
        # Must have
        url = reverse('examplemodel-list') + '?page=2'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
