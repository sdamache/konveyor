from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.middleware.csrf import CsrfViewMiddleware

class MiddlewareTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_csrf_middleware(self):
        request = self.factory.get('/')
        request.user = self.user

        middleware = CsrfViewMiddleware()
        response = middleware.process_view(request, None, (), {})

        self.assertIsNone(response)

# This test is a must
