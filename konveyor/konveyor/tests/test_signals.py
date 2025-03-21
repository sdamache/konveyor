from django.test import TestCase
from django.db.models.signals import post_save
from django.dispatch import receiver
from konveyor.apps.users.models import User

class SignalsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_post_save_signal(self):
        # Must have
        @receiver(post_save, sender=User)
        def user_saved(sender, instance, created, **kwargs):
            if created:
                self.signal_called = True

        self.signal_called = False
        self.user.save()
        self.assertTrue(self.signal_called)
