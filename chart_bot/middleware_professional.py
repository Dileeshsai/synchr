"""
Professional Chart Bot Middleware
"""
from django.utils.deprecation import MiddlewareMixin
from django.template.loader import render_to_string
from django.conf import settings
from .models import BotConfiguration
from .authentication import ChartBotAuthentication
import logging

logger = logging.getLogger(__name__)


class ProfessionalChartBotMiddleware(MiddlewareMixin):
    """
    Professional middleware to inject Chart Bot widget into every page
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
            
            # Check if user is authenticated using professional authentication
            user_context = ChartBotAuthentication.get_user_context(request)
            if not user_context:
                return response
            
            # Check if bot is enabled
            try:
                config = BotConfiguration.objects.first()
                if not config or not config.is_enabled:
                    return response
            except Exception as e:
                logger.error(f"Error checking bot configuration: {str(e)}")
                return response
            
            # Inject widget into HTML
            if hasattr(response, 'content'):
                try:
                    content = response.content.decode('utf-8')
                    
                    # Add widget before closing body tag
                    widget_html = self._get_widget_html(request, user_context)
                    if widget_html and '</body>' in content:
                        content = content.replace('</body>', f'{widget_html}</body>')
                        response.content = content.encode('utf-8')
                        
                        logger.info(f"Chart Bot widget injected for user: {user_context['username']}")
                        
                except Exception as e:
                    logger.error(f"Error injecting Chart Bot widget: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error in ProfessionalChartBotMiddleware: {str(e)}")
        
        return response
    
    def _get_widget_html(self, request, user_context):
        """
        Generate professional Chart Bot widget HTML
        """
        try:
            from django.template import Context, Template
            from django.middleware.csrf import get_token
            
            widget_template = """
            {% load static %}
            <div id="chart-bot-container"></div>
            
            <script>
            // Professional Chart Bot Configuration
            window.chartBotConfig = {
                apiEndpoint: '{{ api_endpoint }}',
                statusEndpoint: '{{ status_endpoint }}',
                testAuthEndpoint: '{{ test_auth_endpoint }}',
                autoStart: true,
                position: 'bottom-right',
                theme: 'light',
                debug: {{ debug|yesno:"true,false" }},
                userContext: {
                    username: '{{ user_context.username }}',
                    userId: {{ user_context.user_id }},
                    employeeId: {{ user_context.employee_id|default:"null" }},
                    isStaff: {{ user_context.is_staff|yesno:"true,false" }},
                    isSuperuser: {{ user_context.is_superuser|yesno:"true,false" }}
                }
            };
            </script>
            
            <!-- Load Professional Chart Bot CSS -->
            <link rel="stylesheet" href="{% static 'chart_bot/css/chatbot_professional.css' %}">
            
            <!-- Load Professional Chart Bot JavaScript -->
            <script src="{% static 'chart_bot/js/chatbot_professional.js' %}"></script>
            """
            
            template = Template(widget_template)
            context = Context({
                'api_endpoint': '/chart-bot-v2/api/v2/chat/',
                'status_endpoint': '/chart-bot-v2/api/v2/status/',
                'test_auth_endpoint': '/chart-bot-v2/api/v2/test-auth/',
                'debug': settings.DEBUG,
                'user_context': user_context
            })
            
            return template.render(context)
            
        except Exception as e:
            logger.error(f"Error generating Chart Bot widget HTML: {str(e)}")
            return None
