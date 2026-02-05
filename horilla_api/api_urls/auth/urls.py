from django.urls import path

from ...api_views.auth.views import LoginAPIView, ForgotPasswordAPIView, ResetPasswordAPIView, UserProfileAPIView, ChangePasswordAPIView

urlpatterns = [
    path("login/", LoginAPIView.as_view()),
    path("forgot-password/", ForgotPasswordAPIView.as_view()),
    path("reset-password/", ResetPasswordAPIView.as_view()),
    path("change-password/", ChangePasswordAPIView.as_view()),
    path("profile/", UserProfileAPIView.as_view(), name="user-profile"),
]
