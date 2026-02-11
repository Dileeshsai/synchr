from django.urls import path

from ...api_views.auth.views import (
    ChangePasswordAPIView,
    ForgotPasswordAPIView,
    GroupsListView,
    LoginAPIView,
    PermissionsListView,
    ResetPasswordAPIView,
    UserProfileAPIView,
)

urlpatterns = [
    path("login/", LoginAPIView.as_view()),
    path("forgot-password/", ForgotPasswordAPIView.as_view()),
    path("reset-password/", ResetPasswordAPIView.as_view()),
    path("change-password/", ChangePasswordAPIView.as_view()),
    path("profile/", UserProfileAPIView.as_view(), name="user-profile"),
    path("groups/", GroupsListView.as_view(), name="api-auth-groups"),
    path("permissions/", PermissionsListView.as_view(), name="api-auth-permissions"),
]
