"""
Compatibility URLs for legacy 'employee_ai' namespace.

Provides only the route(s) still referenced by templates so that existing
links keep working after the AI refactor. New functionality lives in the
recruitment module and the LLM processor.
"""

from django.urls import path

from .llm_views import AIDocumentUploadPageView

app_name = "employee_ai"

urlpatterns = [
    path(
        "upload-page/<int:employee_id>/",
        AIDocumentUploadPageView.as_view(),
        name="ai_upload_page",
    ),
]


