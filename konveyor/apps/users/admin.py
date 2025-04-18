from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'modified_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'modified_at') 