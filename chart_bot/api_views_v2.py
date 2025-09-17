"""
Professional API Views for Chart Bot
"""
import json
import uuid
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .authentication import ChartBotAuthentication
from .core.langgraph_agent import ChartBotAgent
from .models import ChatSession, ChatMessage, BotConfiguration

logger = logging.getLogger(__name__)


class ProfessionalChartBotAPIView(APIView):
    """
    Professional Chart Bot API with robust authentication
    """
    permission_classes = [AllowAny]  # We handle auth manually
    
    def post(self, request):
        """
        Process a chat message with professional error handling
        """
        try:
            # Get user context
            user_context = ChartBotAuthentication.get_user_context(request)
            if not user_context:
                logger.warning("Unauthenticated request to Chart Bot API")
                return Response({
                    'success': False,
                    'error': 'authentication_required',
                    'message': 'Please log in to use Chart Bot.',
                    'response': 'Please log in to use Chart Bot.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            user = user_context['user']
            logger.info(f"Chart Bot API called by user: {user.username} (ID: {user.id})")
            
            # Validate request data
            data = request.data
            message = data.get('message', '').strip()
            session_id = data.get('session_id')
            
            if not message:
                return Response({
                    'success': False,
                    'error': 'invalid_request',
                    'message': 'Message is required',
                    'response': 'Please provide a message.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create or get session
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Initialize agent with fallback
            try:
                # Try to use LangGraph agent first
                from .core.langgraph_agent import ChartBotAgent
                agent = ChartBotAgent(user, session_id)
                logger.info("Using LangGraph agent")
            except ImportError:
                # Fallback to simple agent
                logger.info("LangGraph not available, using simple agent")
                from .core.simple_agent import SimpleChartBotAgent
                agent = SimpleChartBotAgent(user, session_id)
            except Exception as e:
                logger.error(f"Failed to initialize Chart Bot agent: {str(e)}")
                # Try simple agent as fallback
                try:
                    from .core.simple_agent import SimpleChartBotAgent
                    agent = SimpleChartBotAgent(user, session_id)
                    logger.info("Using simple agent as fallback")
                except Exception as e2:
                    logger.error(f"Failed to initialize simple agent: {str(e2)}")
                    return Response({
                        'success': False,
                        'error': 'agent_initialization_failed',
                        'message': 'Failed to initialize Chart Bot',
                        'response': 'Sorry, I\'m having trouble starting up. Please try again.'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Process query
            try:
                result = agent.process_query(message)
                
                return Response({
                    'success': result.get('success', True),
                    'response': result.get('response', 'Sorry, I couldn\'t process your request.'),
                    'session_id': result.get('session_id', session_id),
                    'user_role': result.get('user_role', 'unknown'),
                    'timestamp': datetime.now().isoformat(),
                    'user_context': {
                        'username': user.username,
                        'user_id': user.id,
                        'employee_id': user_context.get('employee_id')
                    }
                })
                
            except Exception as e:
                logger.error(f"Error processing query: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'query_processing_failed',
                    'message': 'Failed to process query',
                    'response': 'Sorry, I encountered an error while processing your request. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            logger.error(f"Unexpected error in ChartBotAPIView: {str(e)}")
            return Response({
                'success': False,
                'error': 'internal_server_error',
                'message': 'Internal server error',
                'response': 'Sorry, I encountered an unexpected error. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfessionalBotStatusAPIView(APIView):
    """
    Professional bot status API
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Get bot status and user permissions
        """
        try:
            # Get user context
            user_context = ChartBotAuthentication.get_user_context(request)
            if not user_context:
                return Response({
                    'authenticated': False,
                    'bot_enabled': False,
                    'message': 'Authentication required'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            user = user_context['user']
            
            # Get bot configuration
            try:
                config = BotConfiguration.objects.first()
                if not config:
                    config = BotConfiguration.objects.create(
                        name="Chart Bot",
                        is_enabled=True,
                        llm_endpoint="http://125.18.84.108:11434/api/generate",
                        llm_model="mistral"
                    )
            except Exception as e:
                logger.error(f"Error getting bot configuration: {str(e)}")
                config = None
            
            # Get user security context
            try:
                from .core.security import SecurityManager
                security_manager = SecurityManager(user)
                security_context = security_manager.get_security_context()
            except Exception as e:
                logger.error(f"Error getting security context: {str(e)}")
                security_context = {
                    'user_role': 'unknown',
                    'permissions': {},
                    'accessible_employees': []
                }
            
            return Response({
                'authenticated': True,
                'bot_enabled': config.is_enabled if config else False,
                'bot_name': config.name if config else 'Chart Bot',
                'user_role': security_context.get('user_role', 'unknown'),
                'permissions': security_context.get('permissions', {}),
                'accessible_employees_count': len(security_context.get('accessible_employees', [])),
                'user_context': {
                    'username': user.username,
                    'user_id': user.id,
                    'employee_id': user_context.get('employee_id'),
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser
                },
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error in BotStatusAPIView: {str(e)}")
            return Response({
                'authenticated': False,
                'bot_enabled': False,
                'error': 'internal_server_error',
                'message': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfessionalTestAuthAPIView(APIView):
    """
    Professional authentication test API
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Test authentication with detailed information
        """
        try:
            user_context = ChartBotAuthentication.get_user_context(request)
            
            if user_context:
                return Response({
                    'authenticated': True,
                    'username': user_context['username'],
                    'user_id': user_context['user_id'],
                    'session_key': user_context.get('session_key'),
                    'ip_address': user_context.get('ip_address'),
                    'employee_id': user_context.get('employee_id'),
                    'employee_name': user_context.get('employee_name'),
                    'is_staff': user_context['is_staff'],
                    'is_superuser': user_context['is_superuser'],
                    'is_active': user_context['is_active'],
                    'message': 'Authentication successful',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return Response({
                    'authenticated': False,
                    'message': 'Authentication failed - no valid user found',
                    'session_key': request.session.session_key if hasattr(request, 'session') else None,
                    'session_data': dict(request.session) if hasattr(request, 'session') else {},
                    'timestamp': datetime.now().isoformat()
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            logger.error(f"Error in TestAuthAPIView: {str(e)}")
            return Response({
                'authenticated': False,
                'error': 'internal_server_error',
                'message': f'Authentication test failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Function-based views for backward compatibility
@api_view(['POST'])
@permission_classes([AllowAny])
def professional_chat_endpoint(request):
    """
    Professional function-based chat endpoint
    """
    view = ProfessionalChartBotAPIView()
    return view.post(request)


@api_view(['GET'])
@permission_classes([AllowAny])
def professional_status_endpoint(request):
    """
    Professional function-based status endpoint
    """
    view = ProfessionalBotStatusAPIView()
    return view.get(request)


@api_view(['GET'])
@permission_classes([AllowAny])
def professional_test_auth_endpoint(request):
    """
    Professional function-based auth test endpoint
    """
    view = ProfessionalTestAuthAPIView()
    return view.get(request)


def test_page_view(request):
    """
    Professional test page view for debugging Chart Bot
    """
    from django.http import HttpResponse
    from django.template import Context, Template
    
    # Read the professional test page HTML
    with open('chart_bot/test_page_professional.html', 'r') as f:
        html_content = f.read()
    
    # Add CSRF token
    from django.middleware.csrf import get_token
    csrf_token = get_token(request)
    
    # Replace placeholder with actual CSRF token
    html_content = html_content.replace('{% csrf_token %}', f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">')
    
    return HttpResponse(html_content)
