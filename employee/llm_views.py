from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View

from .models import Employee


class AIDocumentUploadPageView(View):
    """Deprecated placeholder to preserve existing links.

    The legacy Employee AI upload page has been removed in favor of the
    recruitment resume upload flow. This view exists to avoid template
    errors from references to the old URL namespace and to guide users
    to the new entry point.
    """

    def get(self, request, employee_id: int):
        # Ensure the employee exists for 404 correctness
        get_object_or_404(Employee, id=employee_id)
        return HttpResponse(
            "AI Document Processing has moved to Recruitment → Candidates. "
            "Please upload resumes there to auto-fill details.",
            content_type="text/plain",
        )


