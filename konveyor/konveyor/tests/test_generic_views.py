from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from konveyor.apps.api.models import ExampleModel
from konveyor.apps.api.serializers import ExampleModelSerializer

class ExampleModelGenericViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.example_model = ExampleModel.objects.create(name='Test Model', description='Test Description')
        self.valid_payload = {
            'name': 'New Model',
            'description': 'New Description'
        }
        self.invalid_payload = {
            'name': '',
            'description': 'New Description'
        }

    def test_get_all_example_models(self):
        # Must have
        response = self.client.get(reverse('examplemodel-list'))
        example_models = ExampleModel.objects.all()
        serializer = ExampleModelSerializer(example_models, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_valid_example_model(self):
        # Must have
        response = self.client.post(
            reverse('examplemodel-list'),
            data=self.valid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_invalid_example_model(self):
        # Must have
        response = self.client.post(
            reverse('examplemodel-list'),
            data=self.invalid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_valid_single_example_model(self):
        # Must have
        response = self.client.get(reverse('examplemodel-detail', kwargs={'pk': self.example_model.pk}))
        example_model = ExampleModel.objects.get(pk=self.example_model.pk)
        serializer = ExampleModelSerializer(example_model)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid_single_example_model(self):
        # Must have
        response = self.client.get(reverse('examplemodel-detail', kwargs={'pk': 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_valid_update_example_model(self):
        # Must have
        response = self.client.put(
            reverse('examplemodel-detail', kwargs={'pk': self.example_model.pk}),
            data=self.valid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_update_example_model(self):
        # Must have
        response = self.client.put(
            reverse('examplemodel-detail', kwargs={'pk': self.example_model.pk}),
            data=self.invalid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_delete_example_model(self):
        # Must have
        response = self.client.delete(reverse('examplemodel-detail', kwargs={'pk': self.example_model.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_invalid_delete_example_model(self):
        # Must have
        response = self.client.delete(reverse('examplemodel-detail', kwargs={'pk': 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
