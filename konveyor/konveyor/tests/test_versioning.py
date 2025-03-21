from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

class VersioningTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_default_version(self):
        # Must have
        response = self.client.get(reverse('api-root'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['version'], 'v1')

    def test_v1_version(self):
        # Must have
        response = self.client.get(reverse('api-root'), HTTP_ACCEPT='application/vnd.example.v1+json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['version'], 'v1')

    def test_v2_version(self):
        # Must have
        response = self.client.get(reverse('api-root'), HTTP_ACCEPT='application/vnd.example.v2+json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['version'], 'v2')
