from django.test import TestCase
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import User

class BasicAuthenticationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.auth = BasicAuthentication()

    def test_basic_authentication_success(self):
        # Must have
        request = self.factory.get('/')
        request.META['HTTP_AUTHORIZATION'] = 'Basic dGVzdHVzZXI6dGVzdHBhc3N3b3Jk'
        user, _ = self.auth.authenticate(request)
        self.assertEqual(user, self.user)

    def test_basic_authentication_failure(self):
        # Must have
        request = self.factory.get('/')
        request.META['HTTP_AUTHORIZATION'] = 'Basic invalidtoken'
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

class SessionAuthenticationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.auth = SessionAuthentication()

    def test_session_authentication_success(self):
        # Must have
        request = self.factory.get('/')
        force_authenticate(request, user=self.user)
        user, _ = self.auth.authenticate(request)
        self.assertEqual(user, self.user)

    def test_session_authentication_failure(self):
        # Must have
        request = self.factory.get('/')
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

class TokenAuthenticationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.auth = TokenAuthentication()
        self.token = self.auth.get_model().objects.create(user=self.user)

    def test_token_authentication_success(self):
        # Must have
        request = self.factory.get('/')
        request.META['HTTP_AUTHORIZATION'] = f'Token {self.token.key}'
        user, _ = self.auth.authenticate(request)
        self.assertEqual(user, self.user)

    def test_token_authentication_failure(self):
        # Must have
        request = self.factory.get('/')
        request.META['HTTP_AUTHORIZATION'] = 'Token invalidtoken'
        result = self.auth.authenticate(request)
        self.assertIsNone(result)
