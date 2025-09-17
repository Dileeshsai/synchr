"""
URL Configuration for Chart Bot
"""
from django.urls import path, include
from . import api_views

urlpatterns = [
    # API endpoints
    path('api/chat/', api_views.ChartBotAPIView.as_view(), name='chart_bot_chat'),
    path('api/history/', api_views.ChatHistoryAPIView.as_view(), name='chart_bot_history'),
    path('api/sessions/', api_views.ChatSessionsAPIView.as_view(), name='chart_bot_sessions'),
    path('api/status/', api_views.BotStatusAPIView.as_view(), name='chart_bot_status'),
    path('api/test-auth/', api_views.TestAuthAPIView.as_view(), name='chart_bot_test_auth'),
    
    # Test page
    path('test/', api_views.test_page_view, name='chart_bot_test'),
    
    # Legacy endpoints
    path('chat/', api_views.chat_endpoint, name='chart_bot_chat_legacy'),
    path('history/', api_views.chat_history_endpoint, name='chart_bot_history_legacy'),
]
