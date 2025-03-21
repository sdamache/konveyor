from django.test import TestCase
from django.template import Template, Context

class TemplateTest(TestCase):
    def render_template(self, template_string, context=None):
        context = context or {}
        template = Template(template_string)
        return template.render(Context(context))

    def test_base_template(self):
        # Must have
        template_string = """
        {% extends "base.html" %}
        {% block content %}
        <p>Test content</p>
        {% endblock %}
        """
        rendered = self.render_template(template_string)
        self.assertIn("<p>Test content</p>", rendered)
