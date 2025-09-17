"""
Chart Bot Template Tags
"""
from django import template
from django.conf import settings
from ..models import BotConfiguration

register = template.Library()


@register.inclusion_tag('chart_bot/widget.html', takes_context=True)
def chart_bot_widget(context):
    """
    Template tag to include Chart Bot widget
    """
    request = context['request']
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return {}
    
    # Check if bot is enabled
    try:
        config = BotConfiguration.objects.first()
        if not config or not config.is_enabled:
            return {}
    except:
        return {}
    
    return {
        'user': request.user,
        'config': config
    }


@register.simple_tag(takes_context=True)
def chart_bot_enabled(context):
    """
    Check if Chart Bot is enabled
    """
    try:
        config = BotConfiguration.objects.first()
        return config and config.is_enabled
    except:
        return False


@register.simple_tag(takes_context=True)
def chart_bot_config(context):
    """
    Get Chart Bot configuration as JSON
    """
    try:
        config = BotConfiguration.objects.first()
        if config:
            return {
                'name': config.name,
                'enabled': config.is_enabled,
                'endpoint': config.llm_endpoint,
                'model': config.llm_model
            }
    except:
        pass
    
    return {}
