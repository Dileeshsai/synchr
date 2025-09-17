"""
Direct URL Configuration for Chart Bot - Bypasses authentication issues
"""
from django.urls import path
from . import direct_api

urlpatterns = [
    # Direct API endpoints that bypass authentication issues
    path('api/direct/chat/', direct_api.DirectChartBotAPIView.as_view(), name='chart_bot_direct_chat'),
    path('api/direct/status/', direct_api.DirectStatusAPIView.as_view(), name='chart_bot_direct_status'),
    path('api/direct/test-auth/', direct_api.DirectTestAuthAPIView.as_view(), name='chart_bot_direct_test_auth'),
    
    # Function-based endpoints
    path('api/direct/chat-fn/', direct_api.direct_chat_endpoint, name='chart_bot_direct_chat_fn'),
    path('api/direct/status-fn/', direct_api.direct_status_endpoint, name='chart_bot_direct_status_fn'),
    path('api/direct/test-auth-fn/', direct_api.direct_test_auth_endpoint, name='chart_bot_direct_test_auth_fn'),
    
    # Test page
    path('test/', direct_api.direct_test_page_view, name='chart_bot_direct_test'),
]
