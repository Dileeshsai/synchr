"""
Direct Chart Bot Middleware - Bypasses authentication issues
"""
from django.utils.deprecation import MiddlewareMixin
from django.template.loader import render_to_string
from django.conf import settings
from .models import BotConfiguration
from .authentication_fix import DirectAuthFix
import logging

logger = logging.getLogger(__name__)


class DirectChartBotMiddleware(MiddlewareMixin):
    """
    Direct middleware that bypasses authentication issues
    """
    
    def process_response(self, request, response):
        """
        Add Chart Bot widget to HTML responses
        """
        try:
            # Only process HTML responses
            if not response.get('Content-Type', '').startswith('text/html'):
                return response
            
            # Skip for admin pages, API endpoints, and static files
            if (request.path.startswith('/admin/') or 
                request.path.startswith('/api/') or
                request.path.startswith('/chart-bot/') or
                request.path.startswith('/static/') or
                request.path.startswith('/media/')):
                return response
            
            # Always inject widget (bypass authentication check)
            logger.info("🚀 Direct Chart Bot middleware injecting widget")
            
            # Inject widget into HTML
            if hasattr(response, 'content'):
                try:
                    content = response.content.decode('utf-8')
                    
                    # Add widget before closing body tag
                    widget_html = self._get_direct_widget_html(request)
                    if widget_html and '</body>' in content:
                        content = content.replace('</body>', f'{widget_html}</body>')
                        response.content = content.encode('utf-8')
                        
                        logger.info("✅ Direct Chart Bot widget injected successfully")
                        
                except Exception as e:
                    logger.error(f"Error injecting Direct Chart Bot widget: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error in DirectChartBotMiddleware: {str(e)}")
        
        return response
    
    def _get_direct_widget_html(self, request):
        """
        Generate direct Chart Bot widget HTML
        """
        try:
            from django.template import Context, Template
            from django.middleware.csrf import get_token
            
            widget_template = """
            {% load static %}
            <div id="chart-bot-container"></div>
            
            <script>
            // Direct Chart Bot Configuration - Bypasses authentication issues
            window.chartBotConfig = {
                apiEndpoint: '{{ api_endpoint }}',
                statusEndpoint: '{{ status_endpoint }}',
                testAuthEndpoint: '{{ test_auth_endpoint }}',
                autoStart: true,
                position: 'bottom-right',
                theme: 'light',
                debug: {{ debug|yesno:"true,false" }},
                bypassAuth: true
            };
            </script>
            
            <!-- Load Professional Chart Bot CSS -->
            <link rel="stylesheet" href="{% static 'chart_bot/css/chatbot_professional.css' %}">
            
            <!-- Load Professional Chart Bot JavaScript -->
            <script src="{% static 'chart_bot/js/chatbot_professional.js' %}"></script>
            """
            
            template = Template(widget_template)
            context = Context({
                'api_endpoint': '/chart-bot-direct/api/direct/chat/',
                'status_endpoint': '/chart-bot-direct/api/direct/status/',
                'test_auth_endpoint': '/chart-bot-direct/api/direct/test-auth/',
                'debug': settings.DEBUG
            })
            
            return template.render(context)
            
        except Exception as e:
            logger.error(f"Error generating Direct Chart Bot widget HTML: {str(e)}")
            return None
