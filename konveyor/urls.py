"""
URL configuration for konveyor project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from konveyor.apps.core.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/bot/", include("konveyor.apps.bot.urls")
    ),  # Slack bot integration - must be before api/ to avoid conflicts
    path("api/", include("konveyor.apps.api.urls")),
    path("documents/", include("konveyor.apps.documents.urls")),
    # Azure App Service health check endpoint
    path("healthz/", health_check, name="health_check_root"),
    # Core URLs should be last
    path("", include("konveyor.apps.core.urls")),
    # TODO: Add other app-specific URLs when implemented
]

# Add static/media URL mappings for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Try to import debug_toolbar, but don't fail if it's not installed
    try:
        import debug_toolbar

        urlpatterns += [
            path("__debug__/", include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass
