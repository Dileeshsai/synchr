"""
Chart Bot Admin Interface
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import ChatSession, ChatMessage, BotConfiguration


@admin.register(BotConfiguration)
class BotConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for Bot Configuration
    """
    list_display = ['name', 'is_enabled', 'llm_model', 'llm_endpoint', 'max_context_length']
    list_filter = ['is_enabled', 'llm_model']
    search_fields = ['name', 'llm_endpoint']
    
    fieldsets = (
        ('Basic Settings', {
            'fields': ('name', 'is_enabled')
        }),
        ('LLM Configuration', {
            'fields': ('llm_endpoint', 'llm_model', 'response_timeout')
        }),
        ('Performance Settings', {
            'fields': ('max_context_length',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one configuration instance
        return not BotConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the only configuration
        return BotConfiguration.objects.count() > 1


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for Chat Sessions
    """
    list_display = ['session_id', 'user', 'is_active', 'created_at', 'updated_at', 'message_count']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['session_id', 'user__username', 'user__email']
    readonly_fields = ['session_id', 'created_at', 'updated_at']
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('messages')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """
    Admin interface for Chat Messages
    """
    list_display = ['session', 'message_type', 'content_preview', 'timestamp']
    list_filter = ['message_type', 'timestamp', 'session__user']
    search_fields = ['content', 'session__session_id', 'session__user__username']
    readonly_fields = ['timestamp']
    
    def content_preview(self, obj):
        preview = obj.content[:50]
        if len(obj.content) > 50:
            preview += '...'
        return preview
    content_preview.short_description = 'Content Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'session__user')
