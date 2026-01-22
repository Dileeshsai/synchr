from django.urls import path
from ...api_views.recruitment import views

urlpatterns = [
    path("recruitments/", views.RecruitmentAPIView.as_view(), name="api-recruitment-list"),
    path("recruitments/<int:pk>/", views.RecruitmentAPIView.as_view(), name="api-recruitment-detail"),
    path("candidates/", views.CandidateAPIView.as_view(), name="api-candidate-list"),
    path("candidates/<int:pk>/", views.CandidateAPIView.as_view(), name="api-candidate-detail"),
    path("stages/", views.StageAPIView.as_view(), name="api-stage-list"),
    path("stages/<int:pk>/", views.StageAPIView.as_view(), name="api-stage-detail"),
    path("interviews/", views.InterviewScheduleAPIView.as_view(), name="api-interview-list"),
    path("interviews/<int:pk>/", views.InterviewScheduleAPIView.as_view(), name="api-interview-detail"),
    path("survey-templates/", views.SurveyTemplateAPIView.as_view(), name="api-survey-template-list"),
    path("survey-templates/<int:pk>/", views.SurveyTemplateAPIView.as_view(), name="api-survey-template-detail"),
    path("skills/", views.SkillAPIView.as_view(), name="api-skill-list"),
    path("skills/<int:pk>/", views.SkillAPIView.as_view(), name="api-skill-detail"),
]

