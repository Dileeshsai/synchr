"""
Chart Bot Models
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from horilla.models import HorillaModel
from base.horilla_company_manager import HorillaCompanyManager


class ChatSession(HorillaModel):
    """
    Model to store chat sessions for the Chart Bot
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chat_sessions',
        verbose_name=_("User")
    )
    session_id = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name=_("Session ID")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active Session")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )
    
    objects = HorillaCompanyManager()
    
    class Meta:
        verbose_name = _("Chat Session")
        verbose_name_plural = _("Chat Sessions")
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Session {self.session_id} - {self.user.username}"


class ChatMessage(HorillaModel):
    """
    Model to store individual chat messages
    """
    MESSAGE_TYPES = [
        ('user', _('User Message')),
        ('bot', _('Bot Response')),
        ('system', _('System Message')),
    ]
    
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_("Chat Session")
    )
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPES,
        verbose_name=_("Message Type")
    )
    content = models.TextField(
        verbose_name=_("Message Content")
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Message Metadata")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Timestamp")
    )
    
    objects = HorillaCompanyManager()
    
    class Meta:
        verbose_name = _("Chat Message")
        verbose_name_plural = _("Chat Messages")
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."


class BotConfiguration(HorillaModel):
    """
    Model to store Chart Bot configuration settings
    """
    name = models.CharField(
        max_length=100,
        default="Chart Bot",
        verbose_name=_("Bot Name")
    )
    is_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Bot Enabled")
    )
    llm_endpoint = models.URLField(
        default="http://125.18.84.108:11434/api/generate",
        verbose_name=_("LLM Endpoint")
    )
    llm_model = models.CharField(
        max_length=50,
        default="mistral",
        verbose_name=_("LLM Model")
    )
    max_context_length = models.IntegerField(
        default=10,
        verbose_name=_("Max Context Messages")
    )
    response_timeout = models.IntegerField(
        default=30,
        verbose_name=_("Response Timeout (seconds)")
    )
    
    objects = HorillaCompanyManager()
    
    class Meta:
        verbose_name = _("Bot Configuration")
        verbose_name_plural = _("Bot Configurations")
    
    def __str__(self):
        return f"{self.name} - {'Enabled' if self.is_enabled else 'Disabled'}"
