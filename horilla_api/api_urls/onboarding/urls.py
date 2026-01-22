from django.urls import path
from ...api_views.onboarding import views

urlpatterns = [
    path("stages/", views.OnboardingStageAPIView.as_view(), name="api-onboarding-stage-list"),
    path("stages/<int:pk>/", views.OnboardingStageAPIView.as_view(), name="api-onboarding-stage-detail"),
    path("tasks/", views.OnboardingTaskAPIView.as_view(), name="api-onboarding-task-list"),
    path("tasks/<int:pk>/", views.OnboardingTaskAPIView.as_view(), name="api-onboarding-task-detail"),
    path("candidate-stages/", views.CandidateStageAPIView.as_view(), name="api-candidate-stage-list"),
    path("candidate-stages/<int:pk>/", views.CandidateStageAPIView.as_view(), name="api-candidate-stage-detail"),
    path("candidate-tasks/", views.CandidateTaskAPIView.as_view(), name="api-candidate-task-list"),
    path("candidate-tasks/<int:pk>/", views.CandidateTaskAPIView.as_view(), name="api-candidate-task-detail"),
    path("portals/", views.OnboardingPortalAPIView.as_view(), name="api-onboarding-portal-list"),
    path("portals/<int:pk>/", views.OnboardingPortalAPIView.as_view(), name="api-onboarding-portal-detail"),
]

