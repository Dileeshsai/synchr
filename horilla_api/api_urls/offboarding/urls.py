from django.urls import path
from ...api_views.offboarding import views

urlpatterns = [
    path("offboardings/", views.OffboardingAPIView.as_view(), name="api-offboarding-list"),
    path("offboardings/<int:pk>/", views.OffboardingAPIView.as_view(), name="api-offboarding-detail"),
    path("stages/", views.OffboardingStageAPIView.as_view(), name="api-offboarding-stage-list"),
    path("stages/<int:pk>/", views.OffboardingStageAPIView.as_view(), name="api-offboarding-stage-detail"),
    path("employees/", views.OffboardingEmployeeAPIView.as_view(), name="api-offboarding-employee-list"),
    path("employees/<int:pk>/", views.OffboardingEmployeeAPIView.as_view(), name="api-offboarding-employee-detail"),
    path("resignation-letters/", views.ResignationLetterAPIView.as_view(), name="api-resignation-letter-list"),
    path("resignation-letters/<int:pk>/", views.ResignationLetterAPIView.as_view(), name="api-resignation-letter-detail"),
    path("tasks/", views.OffboardingTaskAPIView.as_view(), name="api-offboarding-task-list"),
    path("tasks/<int:pk>/", views.OffboardingTaskAPIView.as_view(), name="api-offboarding-task-detail"),
    path("employee-tasks/", views.EmployeeTaskAPIView.as_view(), name="api-employee-task-list"),
    path("employee-tasks/<int:pk>/", views.EmployeeTaskAPIView.as_view(), name="api-employee-task-detail"),
    path("exit-reasons/", views.ExitReasonAPIView.as_view(), name="api-exit-reason-list"),
    path("exit-reasons/<int:pk>/", views.ExitReasonAPIView.as_view(), name="api-exit-reason-detail"),
    path("notes/", views.OffboardingNoteAPIView.as_view(), name="api-offboarding-note-list"),
    path("notes/<int:pk>/", views.OffboardingNoteAPIView.as_view(), name="api-offboarding-note-detail"),
    path("settings/", views.OffboardingGeneralSettingAPIView.as_view(), name="api-offboarding-setting-list"),
    path("settings/<int:pk>/", views.OffboardingGeneralSettingAPIView.as_view(), name="api-offboarding-setting-detail"),
]

