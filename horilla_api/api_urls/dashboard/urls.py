"""Dashboard API URLs."""

from django.urls import path

from horilla_api.api_views.dashboard.views import (
    EmployeeWorkInfoCompleteAPIView,
    FeedbacksToAnswerAPIView,
    LeaveRequestsToApproveAPIView,
    MainDashboardAPIView,
)

urlpatterns = [
    path("", MainDashboardAPIView.as_view(), name="api-main-dashboard"),
    path(
        "employee-work-info/",
        EmployeeWorkInfoCompleteAPIView.as_view(),
        name="api-dashboard-employee-work-info",
    ),
    path(
        "leave-requests-to-approve/",
        LeaveRequestsToApproveAPIView.as_view(),
        name="api-dashboard-leave-requests-to-approve",
    ),
    path(
        "feedbacks-to-answer/",
        FeedbacksToAnswerAPIView.as_view(),
        name="api-dashboard-feedbacks-to-answer",
    ),
]
