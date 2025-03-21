from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.throttling import UserRateThrottle
from django.urls import reverse
from django.contrib.auth.models import User

class ThrottlingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

    def test_throttling(self):
        url = reverse('api-endpoint')
        for _ in range(UserRateThrottle().rate):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 429)

# This test is a must-have as it ensures that the API endpoint is properly throttled to prevent abuse.
