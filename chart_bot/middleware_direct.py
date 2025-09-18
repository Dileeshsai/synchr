"""
SYNC AI Middleware - Bypasses authentication issues
"""
from django.utils.deprecation import MiddlewareMixin
from django.template.loader import render_to_string
from django.conf import settings
from .models import BotConfiguration
from .authentication_fix import DirectAuthFix
import logging

logger = logging.getLogger(__name__)


class SyncAIMiddleware(MiddlewareMixin):
    """
    Direct middleware that bypasses authentication issues
    """
    
    def process_response(self, request, response):
        """
        Add SYNC AI widget to HTML responses
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
            logger.info("🚀 SYNC AI middleware injecting widget")
            logger.info(f"🚀 SYNC AI middleware - Request path: {request.path}")
            logger.info(f"🚀 SYNC AI middleware - Content-Type: {response.get('Content-Type', '')}")
            
            # Inject widget into HTML
            if hasattr(response, 'content'):
                try:
                    content = response.content.decode('utf-8')
                    
                    # Add widget before closing body tag
                    widget_html = self._get_direct_widget_html(request)
                    if widget_html and '</body>' in content:
                        content = content.replace('</body>', f'{widget_html}</body>')
                        response.content = content.encode('utf-8')
                        
                        logger.info("✅ SYNC AI widget injected successfully")
                        logger.info(f"✅ Widget HTML length: {len(widget_html)} characters")
                    else:
                        logger.warning(f"❌ Widget injection failed - widget_html: {bool(widget_html)}, body tag: {'</body>' in content}")
                        
                except Exception as e:
                    logger.error(f"Error injecting SYNC AI widget: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error in SyncAIMiddleware: {str(e)}")
        
        return response
    
    def _get_direct_widget_html(self, request):
        """
        Generate SYNC AI widget HTML
        """
        try:
            from django.template import Context, Template
            from django.middleware.csrf import get_token
            
            widget_template = """
            {% load static %}
            <div id="chart-bot-container"></div>
            
            <script>
            // SYNC AI Configuration - Bypasses authentication issues
            window.chartBotConfig = {
                apiEndpoint: '{{ api_endpoint }}',
                statusEndpoint: '{{ status_endpoint }}',
                testAuthEndpoint: '{{ test_auth_endpoint }}',
                autoStart: true,
                position: 'bottom-right',
                theme: 'light',
                debug: {{ debug|yesno:"true,false" }},
                bypassAuth: true,
                startMinimized: true
            };
            </script>
            
            <!-- Load Professional SYNC AI CSS -->
            <link rel="stylesheet" href="{% static 'chart_bot/css/chatbot_professional.css' %}">
            
            <!-- Load Professional SYNC AI JavaScript -->
            <script src="{% static 'chart_bot/js/chatbot_professional.js' %}"></script>
            
            <!-- Fallback test widget -->
            <script>
            // Simple fallback test
            setTimeout(function() {
                if (!window.chartBot) {
                    console.log('SYNC AI Bot: Fallback test widget creating...');
                    var testWidget = document.createElement('div');
                    testWidget.innerHTML = '🤖';
                    testWidget.style.cssText = 'position:fixed;bottom:20px;right:80px;width:60px;height:60px;background:white;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:28px;box-shadow:0 8px 25px rgba(0,0,0,0.3);border:2px solid rgba(255,255,255,0.9);z-index:99999;';
                    testWidget.id = 'sync-ai-fallback';
                    document.body.appendChild(testWidget);
                    console.log('SYNC AI Bot: Fallback widget created');
                }
            }, 3000);
            </script>
            """
            
            template = Template(widget_template)
            context = Context({
                'api_endpoint': '/chart-bot-direct/api/direct/chat/',
                'status_endpoint': '/chart-bot-direct/api/direct/status/',
                'test_auth_endpoint': '/chart-bot-direct/api/direct/test-auth/',
                'debug': settings.DEBUG
            })
            
            widget_html = template.render(context)
            logger.info(f"🚀 SYNC AI widget HTML generated: {len(widget_html)} characters")
            return widget_html
            
        except Exception as e:
            logger.error(f"Error generating SYNC AI widget HTML: {str(e)}")
            return None
