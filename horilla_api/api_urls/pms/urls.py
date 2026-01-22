from django.urls import path
from ...api_views.pms import views

urlpatterns = [
    path("periods/", views.PeriodAPIView.as_view(), name="api-period-list"),
    path("periods/<int:pk>/", views.PeriodAPIView.as_view(), name="api-period-detail"),
    path("key-results/", views.KeyResultAPIView.as_view(), name="api-key-result-list"),
    path("key-results/<int:pk>/", views.KeyResultAPIView.as_view(), name="api-key-result-detail"),
    path("objectives/", views.ObjectiveAPIView.as_view(), name="api-objective-list"),
    path("objectives/<int:pk>/", views.ObjectiveAPIView.as_view(), name="api-objective-detail"),
    path("employee-objectives/", views.EmployeeObjectiveAPIView.as_view(), name="api-employee-objective-list"),
    path("employee-objectives/<int:pk>/", views.EmployeeObjectiveAPIView.as_view(), name="api-employee-objective-detail"),
    path("employee-key-results/", views.EmployeeKeyResultAPIView.as_view(), name="api-employee-key-result-list"),
    path("employee-key-results/<int:pk>/", views.EmployeeKeyResultAPIView.as_view(), name="api-employee-key-result-detail"),
    path("feedback/", views.FeedbackAPIView.as_view(), name="api-feedback-list"),
    path("feedback/<int:pk>/", views.FeedbackAPIView.as_view(), name="api-feedback-detail"),
    path("question-templates/", views.QuestionTemplateAPIView.as_view(), name="api-question-template-list"),
    path("question-templates/<int:pk>/", views.QuestionTemplateAPIView.as_view(), name="api-question-template-detail"),
    path("questions/", views.QuestionAPIView.as_view(), name="api-question-list"),
    path("questions/<int:pk>/", views.QuestionAPIView.as_view(), name="api-question-detail"),
    path("question-options/", views.QuestionOptionsAPIView.as_view(), name="api-question-options-list"),
    path("question-options/<int:pk>/", views.QuestionOptionsAPIView.as_view(), name="api-question-options-detail"),
    path("answers/", views.AnswerAPIView.as_view(), name="api-answer-list"),
    path("answers/<int:pk>/", views.AnswerAPIView.as_view(), name="api-answer-detail"),
    path("meetings/", views.MeetingsAPIView.as_view(), name="api-meetings-list"),
    path("meetings/<int:pk>/", views.MeetingsAPIView.as_view(), name="api-meetings-detail"),
    path("meetings-answers/", views.MeetingsAnswerAPIView.as_view(), name="api-meetings-answer-list"),
    path("meetings-answers/<int:pk>/", views.MeetingsAnswerAPIView.as_view(), name="api-meetings-answer-detail"),
    path("employee-bonus-points/", views.EmployeeBonusPointAPIView.as_view(), name="api-employee-bonus-point-list"),
    path("employee-bonus-points/<int:pk>/", views.EmployeeBonusPointAPIView.as_view(), name="api-employee-bonus-point-detail"),
    path("bonus-point-settings/", views.BonusPointSettingAPIView.as_view(), name="api-bonus-point-setting-list"),
    path("bonus-point-settings/<int:pk>/", views.BonusPointSettingAPIView.as_view(), name="api-bonus-point-setting-detail"),
]

