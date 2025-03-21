from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('konveyor.apps.api.urls')),
    path('users/', include('konveyor.apps.users.urls')),
]
