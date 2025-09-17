"""
Professional Authentication System for Chart Bot
"""
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ChartBotAuthentication:
    """
    Professional authentication handler for Chart Bot
    """
    
    @staticmethod
    def get_user_from_request(request):
        """
        Get authenticated user from request with multiple fallback methods
        """
        # Method 1: Direct user authentication
        if hasattr(request, 'user') and request.user.is_authenticated:
            logger.info(f"User authenticated via request.user: {request.user.username}")
            return request.user
        
        # Method 2: Session-based authentication
        session_key = request.session.session_key
        if session_key:
            try:
                session = Session.objects.get(session_key=session_key)
                if session.expire_date > timezone.now():
                    user_id = session.get_decoded().get('_auth_user_id')
                    if user_id:
                        user = User.objects.get(id=user_id)
                        logger.info(f"User authenticated via session: {user.username}")
                        return user
            except (Session.DoesNotExist, User.DoesNotExist) as e:
                logger.warning(f"Session authentication failed: {str(e)}")
        
        # Method 3: Check for authentication in session data
        if hasattr(request, 'session'):
            user_id = request.session.get('_auth_user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    logger.info(f"User authenticated via session data: {user.username}")
                    return user
                except User.DoesNotExist:
                    logger.warning(f"User ID {user_id} not found in database")
        
        # Method 4: Check for custom authentication headers
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            # Handle token-based authentication if needed
            pass
        
        logger.warning("No valid authentication found")
        return None
    
    @staticmethod
    def is_user_authenticated(request):
        """
        Check if user is properly authenticated
        """
        user = ChartBotAuthentication.get_user_from_request(request)
        return user is not None
    
    @staticmethod
    def get_user_context(request):
        """
        Get comprehensive user context for Chart Bot
        """
        user = ChartBotAuthentication.get_user_from_request(request)
        if not user:
            return None
        
        context = {
            'user': user,
            'username': user.username,
            'user_id': user.id,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'session_key': request.session.session_key if hasattr(request, 'session') else None,
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100]
        }
        
        # Add employee information if available
        try:
            if hasattr(user, 'employee_get'):
                employee = user.employee_get
                context.update({
                    'employee_id': employee.id,
                    'employee_name': employee.get_full_name(),
                    'employee_email': employee.email,
                    'employee_active': employee.is_active
                })
        except Exception as e:
            logger.warning(f"Could not get employee info: {str(e)}")
        
        return context
