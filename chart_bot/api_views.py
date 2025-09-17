"""
API Views for Chart Bot
"""
import json
import uuid
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
import logging

from .core.langgraph_agent import ChartBotAgent
from .models import ChatSession, ChatMessage, BotConfiguration

logger = logging.getLogger(__name__)


class BaseChartBotAPIView(APIView):
    """
    Base API view with common authentication logic
    """
    permission_classes = []  # Temporarily remove authentication requirement for debugging
    
    def _get_user_from_request(self, request):
        """
        Get user from request, trying both request.user and session
        """
        user = request.user
        if not user.is_authenticated:
            # Try to get user from session
            user_id = request.session.get('_auth_user_id')
            if user_id:
                from django.contrib.auth.models import User
                try:
                    user = User.objects.get(id=user_id)
                    logger.info(f"Retrieved user from session: {user.username}")
                except User.DoesNotExist:
                    logger.warning("User ID in session but user doesn't exist")
                    return None
            else:
                logger.warning("No user ID in session")
                return None
        return user


class ChartBotAPIView(BaseChartBotAPIView):
    """
    Main API endpoint for Chart Bot
    """
    permission_classes = []  # Temporarily remove authentication requirement for debugging
    
    def post(self, request):
        """
        Process a chat message
        """
        try:
            # Debug logging
            logger.info(f"Chart Bot API called by user: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
            logger.info(f"User authenticated: {request.user.is_authenticated}")
            logger.info(f"Session key: {request.session.session_key}")
            
            # Get user from request
            user = self._get_user_from_request(request)
            if not user:
                return Response({
                    'error': 'Authentication required',
                    'response': 'Please log in to use Chart Bot.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data
            message = data.get('message', '').strip()
            session_id = data.get('session_id')
            
            if not message:
                return Response({
                    'error': 'Message is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create or get session
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Initialize agent
            agent = ChartBotAgent(user, session_id)
            
            # Process query
            result = agent.process_query(message)
            
            return Response({
                'response': result['response'],
                'session_id': result['session_id'],
                'user_role': result.get('user_role'),
                'success': result['success']
            })
            
        except Exception as e:
            logger.error(f"Error in ChartBotAPIView: {str(e)}")
            return Response({
                'error': 'Internal server error',
                'response': 'Sorry, I encountered an error while processing your request. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatHistoryAPIView(BaseChartBotAPIView):
    """
    API endpoint for chat history
    """
    
    def get(self, request):
        """
        Get chat history for a session
        """
        try:
            # Get user from session
            user = self._get_user_from_request(request)
            if not user:
                return Response({
                    'error': 'Authentication required'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            session_id = request.GET.get('session_id')
            limit = int(request.GET.get('limit', 10))
            
            if not session_id:
                return Response({
                    'error': 'Session ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize agent
            agent = ChartBotAgent(user, session_id)
            
            # Get history
            history = agent.get_conversation_history(limit)
            
            return Response({
                'history': history,
                'session_id': session_id
            })
            
        except Exception as e:
            logger.error(f"Error in ChatHistoryAPIView: {str(e)}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatSessionsAPIView(APIView):
    """
    API endpoint for managing chat sessions
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get user's chat sessions
        """
        try:
            sessions = ChatSession.objects.filter(
                user=request.user,
                is_active=True
            ).order_by('-updated_at')[:10]
            
            session_data = []
            for session in sessions:
                session_data.append({
                    'session_id': session.session_id,
                    'created_at': session.created_at,
                    'updated_at': session.updated_at,
                    'message_count': session.messages.count()
                })
            
            return Response({
                'sessions': session_data
            })
            
        except Exception as e:
            logger.error(f"Error in ChatSessionsAPIView: {str(e)}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """
        Create a new chat session
        """
        try:
            session_id = str(uuid.uuid4())
            
            session = ChatSession.objects.create(
                user=request.user,
                session_id=session_id,
                is_active=True
            )
            
            return Response({
                'session_id': session_id,
                'created_at': session.created_at
            })
            
        except Exception as e:
            logger.error(f"Error creating chat session: {str(e)}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """
        Delete a chat session
        """
        try:
            session_id = request.data.get('session_id')
            
            if not session_id:
                return Response({
                    'error': 'Session ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            session = ChatSession.objects.get(
                session_id=session_id,
                user=request.user
            )
            session.is_active = False
            session.save()
            
            return Response({
                'message': 'Session deleted successfully'
            })
            
        except ChatSession.DoesNotExist:
            return Response({
                'error': 'Session not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting chat session: {str(e)}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BotStatusAPIView(BaseChartBotAPIView):
    """
    API endpoint for bot status and configuration
    """
    
    def get(self, request):
        """
        Get bot status and user permissions
        """
        try:
            # Get user from request
            user = self._get_user_from_request(request)
            if not user:
                return Response({
                    'error': 'Authentication required'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get bot configuration
            config = BotConfiguration.objects.first()
            if not config:
                config = BotConfiguration.objects.create()
            
            # Get user security context
            from .core.security import SecurityManager
            security_manager = SecurityManager(user)
            security_context = security_manager.get_security_context()
            
            return Response({
                'bot_enabled': config.is_enabled,
                'bot_name': config.name,
                'user_role': security_context['user_role'],
                'permissions': security_context['permissions'],
                'accessible_employees_count': len(security_context['accessible_employees'])
            })
            
        except Exception as e:
            logger.error(f"Error in BotStatusAPIView: {str(e)}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TestAuthAPIView(BaseChartBotAPIView):
    """
    Test authentication endpoint for debugging
    """
    
    def get(self, request):
        """
        Test authentication
        """
        user = self._get_user_from_request(request)
        return Response({
            'authenticated': user is not None,
            'username': user.username if user else None,
            'user_id': user.id if user else None,
            'session_key': request.session.session_key,
            'session_user_id': request.session.get('_auth_user_id'),
            'message': 'Authentication test successful' if user else 'Authentication failed'
        })


def test_page_view(request):
    """
    Test page view for debugging Chart Bot
    """
    from django.http import HttpResponse
    from django.template import Context, Template
    
    # Read the test page HTML
    with open('chart_bot/test_page.html', 'r') as f:
        html_content = f.read()
    
    # Add CSRF token
    from django.middleware.csrf import get_token
    csrf_token = get_token(request)
    
    # Replace placeholder with actual CSRF token
    html_content = html_content.replace('{% csrf_token %}', f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">')
    
    return HttpResponse(html_content)


# Legacy function-based views for backward compatibility
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def chat_endpoint(request):
    """
    Legacy chat endpoint
    """
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not message:
            return JsonResponse({
                'error': 'Message is required'
            }, status=400)
        
        # Create or get session
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Initialize agent
        agent = ChartBotAgent(request.user, session_id)
        
        # Process query
        result = agent.process_query(message)
        
        return JsonResponse({
            'response': result['response'],
            'session_id': result['session_id'],
            'user_role': result.get('user_role'),
            'success': result['success']
        })
        
    except Exception as e:
        logger.error(f"Error in chat_endpoint: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error',
            'response': 'Sorry, I encountered an error while processing your request. Please try again.'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@login_required
def chat_history_endpoint(request):
    """
    Legacy chat history endpoint
    """
    try:
        session_id = request.GET.get('session_id')
        limit = int(request.GET.get('limit', 10))
        
        if not session_id:
            return JsonResponse({
                'error': 'Session ID is required'
            }, status=400)
        
        # Initialize agent
        agent = ChartBotAgent(request.user, session_id)
        
        # Get history
        history = agent.get_conversation_history(limit)
        
        return JsonResponse({
            'history': history,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error in chat_history_endpoint: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error'
        }, status=500)