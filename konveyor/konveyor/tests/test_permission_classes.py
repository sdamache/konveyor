from django.test import TestCase
from rest_framework.permissions import IsAuthenticated
from konveyor.apps.api.permissions import CustomPermission

class CustomPermissionTest(TestCase):
    def setUp(self):
        self.permission = CustomPermission()

    def test_has_permission_authenticated(self):
        # Must have
        request = self.factory.get('/')
        request.user = self.user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_has_permission_unauthenticated(self):
        # Must have
        request = self.factory.get('/')
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))

class IsAuthenticatedTest(TestCase):
    def setUp(self):
        self.permission = IsAuthenticated()

    def test_has_permission_authenticated(self):
        # Must have
        request = self.factory.get('/')
        request.user = self.user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_has_permission_unauthenticated(self):
        # Must have
        request = self.factory.get('/')
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))
