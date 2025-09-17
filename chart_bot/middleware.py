"""
Chart Bot Middleware
Adds Chart Bot widget to every page
"""
from django.utils.deprecation import MiddlewareMixin
from django.template.loader import render_to_string
from django.conf import settings
from .models import BotConfiguration


class ChartBotMiddleware(MiddlewareMixin):
    """
    Middleware to inject Chart Bot widget into every page
    """
    
    def process_response(self, request, response):
        """
        Add Chart Bot widget to HTML responses
        """
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
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return response
        
        # Check if bot is enabled
        try:
            config = BotConfiguration.objects.first()
            if not config or not config.is_enabled:
                return response
        except Exception as e:
            # Log error but don't break the page
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error checking bot configuration: {str(e)}")
            return response
        
        # Inject widget into HTML
        if hasattr(response, 'content'):
            try:
                content = response.content.decode('utf-8')
                
                # Add widget before closing body tag
                widget_html = self._get_widget_html(request)
                if widget_html and '</body>' in content:
                    content = content.replace('</body>', f'{widget_html}</body>')
                    response.content = content.encode('utf-8')
            except Exception as e:
                # Log error but don't break the page
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error injecting Chart Bot widget: {str(e)}")
        
        return response
    
    def _get_widget_html(self, request):
        """
        Generate Chart Bot widget HTML
        """
        try:
            from django.template import Context, Template
            
            widget_template = """
            {% load static %}
            <div id="chart-bot-container"></div>
            
            <script>
            // Chart Bot Configuration
            window.chartBotConfig = {
                apiEndpoint: '{{ api_endpoint }}',
                historyEndpoint: '{{ history_endpoint }}',
                statusEndpoint: '{{ status_endpoint }}',
                sessionsEndpoint: '{{ sessions_endpoint }}',
                autoStart: true,
                position: 'bottom-right',
                theme: 'light'
            };
            </script>
            
            <!-- Load Chart Bot CSS -->
            <link rel="stylesheet" href="{% static 'chart_bot/css/chatbot.css' %}">
            
            <!-- Load Chart Bot JavaScript -->
            <script src="{% static 'chart_bot/js/chatbot.js' %}"></script>
            """
            
            template = Template(widget_template)
            context = Context({
                'api_endpoint': '/chart-bot/api/chat/',
                'history_endpoint': '/chart-bot/api/history/',
                'status_endpoint': '/chart-bot/api/status/',
                'sessions_endpoint': '/chart-bot/api/sessions/',
            })
            
            return template.render(context)
            
        except Exception as e:
            # Log error but don't break the page
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating Chart Bot widget: {str(e)}")
            return None
