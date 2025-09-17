from django.urls import path

from ...api_views.auth.views import LoginAPIView, ForgotPasswordAPIView,UserProfileAPIView

urlpatterns = [
    path("login/", LoginAPIView.as_view()),
    path("forgot-password/", ForgotPasswordAPIView.as_view()),
    path("profile/", UserProfileAPIView.as_view(), name="user-profile"),
    ]
