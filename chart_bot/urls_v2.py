"""
Professional URL Configuration for Chart Bot
"""
from django.urls import path, include
from . import api_views_v2

urlpatterns = [
    # Professional API endpoints
    path('api/v2/chat/', api_views_v2.ProfessionalChartBotAPIView.as_view(), name='chart_bot_chat_v2'),
    path('api/v2/status/', api_views_v2.ProfessionalBotStatusAPIView.as_view(), name='chart_bot_status_v2'),
    path('api/v2/test-auth/', api_views_v2.ProfessionalTestAuthAPIView.as_view(), name='chart_bot_test_auth_v2'),
    
    # Function-based endpoints for compatibility
    path('api/v2/chat-fn/', api_views_v2.professional_chat_endpoint, name='chart_bot_chat_fn'),
    path('api/v2/status-fn/', api_views_v2.professional_status_endpoint, name='chart_bot_status_fn'),
    path('api/v2/test-auth-fn/', api_views_v2.professional_test_auth_endpoint, name='chart_bot_test_auth_fn'),
    
    # Test page
    path('test/', api_views_v2.test_page_view, name='chart_bot_test'),
]
