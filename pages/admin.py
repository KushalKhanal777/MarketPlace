from django.contrib import admin

from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Admin configuration for Page model."""
    list_display = ('id', 'title', 'slug', 'is_published', 'created_at', 'updated_at')
    list_display_links = ('id', 'title')
    search_fields = ('title', 'content')
    list_filter = ('is_published', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
