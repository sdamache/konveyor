from django.test import TestCase
from konveyor.apps.api.filters import ExampleModelFilter
from konveyor.apps.api.models import ExampleModel

class ExampleModelFilterTest(TestCase):
    def setUp(self):
        self.example_model_1 = ExampleModel.objects.create(name='Test Model 1', description='Description 1')
        self.example_model_2 = ExampleModel.objects.create(name='Test Model 2', description='Description 2')

    def test_filter_by_name(self):
        # Must have
        filterset = ExampleModelFilter(data={'name': 'Test Model 1'})
        queryset = filterset.qs
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.example_model_1)

    def test_filter_by_description(self):
        # Must have
        filterset = ExampleModelFilter(data={'description': 'Description 2'})
        queryset = filterset.qs
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.example_model_2)
