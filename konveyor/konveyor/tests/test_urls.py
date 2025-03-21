from django.test import SimpleTestCase
from django.urls import reverse, resolve
from konveyor.apps.api.views import ExampleModelViewSet
from konveyor.apps.users.views import UserViewSet

class TestUrls(SimpleTestCase):

    def test_examplemodel_list_url_is_resolved(self):
        # Must have
        url = reverse('examplemodel-list')
        self.assertEqual(resolve(url).func.cls, ExampleModelViewSet)

    def test_examplemodel_detail_url_is_resolved(self):
        # Must have
        url = reverse('examplemodel-detail', kwargs={'pk': 1})
        self.assertEqual(resolve(url).func.cls, ExampleModelViewSet)

    def test_user_list_url_is_resolved(self):
        # Must have
        url = reverse('user-list')
        self.assertEqual(resolve(url).func.cls, UserViewSet)

    def test_user_detail_url_is_resolved(self):
        # Must have
        url = reverse('user-detail', kwargs={'pk': 1})
        self.assertEqual(resolve(url).func.cls, UserViewSet)
