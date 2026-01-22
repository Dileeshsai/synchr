from django.urls import path
from ...api_views.project import views

urlpatterns = [
    path("projects/", views.ProjectAPIView.as_view(), name="api-project-list"),
    path("projects/<int:pk>/", views.ProjectAPIView.as_view(), name="api-project-detail"),
    path("stages/", views.ProjectStageAPIView.as_view(), name="api-project-stage-list"),
    path("stages/<int:pk>/", views.ProjectStageAPIView.as_view(), name="api-project-stage-detail"),
    path("tasks/", views.TaskAPIView.as_view(), name="api-task-list"),
    path("tasks/<int:pk>/", views.TaskAPIView.as_view(), name="api-task-detail"),
    path("timesheets/", views.TimeSheetAPIView.as_view(), name="api-timesheet-list"),
    path("timesheets/<int:pk>/", views.TimeSheetAPIView.as_view(), name="api-timesheet-detail"),
]

