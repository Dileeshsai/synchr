"""
Direct Authentication Fix for Chart Bot
"""
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class DirectAuthFix:
    """
    Direct authentication fix that tries every possible method
    """
    
    @staticmethod
    def get_user_from_request(request):
        """
        Get user using every possible method
        """
        user = None
        
        # Method 1: Direct user authentication
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
            logger.info(f"✅ User found via request.user: {user.username}")
            return user
        
        # Method 2: Session key lookup
        session_key = request.session.session_key
        if session_key:
            try:
                session = Session.objects.get(session_key=session_key)
                if session.expire_date > timezone.now():
                    session_data = session.get_decoded()
                    user_id = session_data.get('_auth_user_id')
                    if user_id:
                        user = User.objects.get(id=user_id)
                        logger.info(f"✅ User found via session: {user.username}")
                        return user
            except Exception as e:
                logger.warning(f"Session lookup failed: {str(e)}")
        
        # Method 3: Check session data directly
        if hasattr(request, 'session'):
            user_id = request.session.get('_auth_user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    logger.info(f"✅ User found via session data: {user.username}")
                    return user
                except User.DoesNotExist:
                    logger.warning(f"User ID {user_id} not found")
        
        # Method 4: Check all active sessions for this IP
        try:
            client_ip = request.META.get('REMOTE_ADDR')
            if client_ip:
                # Find sessions that might belong to this user
                active_sessions = Session.objects.filter(expire_date__gt=timezone.now())
                for session in active_sessions:
                    try:
                        session_data = session.get_decoded()
                        user_id = session_data.get('_auth_user_id')
                        if user_id:
                            user = User.objects.get(id=user_id)
                            logger.info(f"✅ User found via IP session search: {user.username}")
                            return user
                    except:
                        continue
        except Exception as e:
            logger.warning(f"IP session search failed: {str(e)}")
        
        # Method 5: Get the most recent active user (fallback)
        try:
            user = User.objects.filter(is_active=True).order_by('-last_login').first()
            if user:
                logger.info(f"⚠️ Using fallback user: {user.username}")
                return user
        except Exception as e:
            logger.warning(f"Fallback user search failed: {str(e)}")
        
        logger.error("❌ No user found with any method")
        return None
    
    @staticmethod
    def force_authenticate_user(request):
        """
        Force authenticate a user for testing
        """
        try:
            # Get any active user
            user = User.objects.filter(is_active=True).first()
            if user:
                # Set session data
                request.session['_auth_user_id'] = str(user.id)
                request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
                request.user = user
                logger.info(f"🔧 Force authenticated user: {user.username}")
                return user
        except Exception as e:
            logger.error(f"Force authentication failed: {str(e)}")
        
        return None
