from django.test import TestCase
from rest_framework.renderers import JSONRenderer
from konveyor.apps.api.models import ExampleModel
from konveyor.apps.api.serializers import ExampleModelSerializer

class JSONRendererTestCase(TestCase):
    def setUp(self):
        self.example_model = ExampleModel.objects.create(name='Test Model', description='Test Description')
        self.serializer = ExampleModelSerializer(self.example_model)

    def test_json_renderer(self):
        # Must have
        renderer = JSONRenderer()
        rendered_data = renderer.render(self.serializer.data)
        self.assertIn(b'"name": "Test Model"', rendered_data)
        self.assertIn(b'"description": "Test Description"', rendered_data)
