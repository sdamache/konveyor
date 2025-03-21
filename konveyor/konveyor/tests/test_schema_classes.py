from django.test import TestCase
from rest_framework.schemas.openapi import SchemaGenerator
from rest_framework.test import APIRequestFactory

class SchemaTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_schema_generation(self):
        # Must have
        generator = SchemaGenerator()
        request = self.factory.get('/openapi')
        schema = generator.get_schema(request=request)
        self.assertIsNotNone(schema)
        self.assertIn('openapi', schema)
        self.assertIn('info', schema)
        self.assertIn('paths', schema)
