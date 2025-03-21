from django.test import TestCase
from django.conf import settings
from django.core.management import call_command
import os

class StaticFilesTest(TestCase):
    def test_collectstatic(self):
        """
        Test that the collectstatic command runs without errors.
        """
        try:
            call_command('collectstatic', interactive=False, verbosity=0)
        except Exception as e:
            self.fail(f"collectstatic command failed: {e}")

    def test_static_files_exist(self):
        """
        Test that the static files are collected and exist in the STATIC_ROOT directory.
        """
        static_root = settings.STATIC_ROOT
        css_file = os.path.join(static_root, 'css', 'styles.css')
        js_file = os.path.join(static_root, 'js', 'scripts.js')

        self.assertTrue(os.path.exists(css_file), f"{css_file} does not exist")
        self.assertTrue(os.path.exists(js_file), f"{js_file} does not exist")
