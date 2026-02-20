from django.db.models import Q
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.filters import (
    RotatingShiftAssignFilters,
    RotatingWorkTypeAssignFilter,
    ShiftRequestFilter,
    WorkTypeRequestFilter,
)
from base.forms import MailTemplateForm
from base.models import (
    FIELD_CHOICE,
    CONDITION_CHOICE,
    AttendanceAllowedIP,
    BiometricAttendance,
    Company,
    Department,
    EmployeeShift,
    EmployeeShiftDay,
    EmployeeShiftSchedule,
    HorillaMailTemplate,
    JobPosition,
    JobRole,
    MultipleApprovalCondition,
    RotatingShift,
    RotatingShiftAssign,
    RotatingWorkType,
    RotatingWorkTypeAssign,
    ShiftRequest,
    WorkType,
    WorkTypeRequest,
)
from base.views import (
    is_reportingmanger,
    rotating_work_type_assign_export,
    shift_request_export,
    work_type_request_export,
)
from employee.models import Actiontype, Employee
from notifications.signals import notify

from ...api_decorators.base.decorators import (
    check_approval_status,
    manager_or_owner_permission_required,
    manager_permission_required,
    permission_required,
)
from ...api_methods.base.methods import groupby_queryset, permission_based_queryset
from ...api_serializers.base.serializers import (
    AttendanceAllowedIPSerializer,
    BiometricAttendanceSerializer,
    BiometricDeviceSerializer,
    CompanySerializer,
    DepartmentSerializer,
    EmployeeShiftDaySerializer,
    EmployeeShiftScheduleSerializer,
    EmployeeShiftSerializer,
    HorillaMailTemplateSerializer,
    JobPositionSerializer,
    JobRoleSerializer,
    MultipleApprovalConditionSerializer,
    RotatingShiftAssignSerializer,
    RotatingShiftSerializer,
    RotatingWorkTypeAssignSerializer,
    RotatingWorkTypeSerializer,
    ShiftRequestSerializer,
    WorkTypeRequestSerializer,
    WorkTypeSerializer,
)


def object_check(cls, pk):
    try:
        obj = cls.objects.get(id=pk)
        return obj
    except cls.DoesNotExist:
        return None


def object_delete(cls, pk):
    try:
        cls.objects.get(id=pk).delete()
        return "", 200
    except Exception as e:
        return {"error": str(e)}, 400


def _get_effective_company_id(request):
    """
    Resolve company ID for filtering Base data (Departments, Job Positions, Job Roles, Companies).
    - If query param company_id is provided and not 'all', use it (admin/superuser with org switcher).
    - Else if the logged-in user has an employee with a company, use that company (scoped user).
    - Else return None (no filter; e.g. superuser viewing all).
    """
    param = request.query_params.get("company_id")
    if param and str(param).strip().lower() not in ("", "all"):
        try:
            return int(param)
        except (TypeError, ValueError):
            pass
    employee = getattr(request.user, "employee_get", None)
    if employee and hasattr(employee, "get_company") and employee.get_company():
        company = employee.get_company()
        return company.id if getattr(company, "id", None) else None
    return None


def individual_permssion_check(request):
    employee_id = request.GET.get("employee_id")
    employee = Employee.objects.filter(id=employee_id).first()
    if request.user.employee_get == employee:
        return True
    elif employee.employee_work_info.reporting_manager_id == request.user.employee_get:
        return True
    elif request.user.has_perm("base.view_rotatingworktypeassign"):
        return True
    return False


def _is_reportingmanger(request, instance):
    """
    If the instance have employee id field then you can use this method to know the request
    user employee is the reporting manager of the instance
    """
    manager = request.user.employee_get
    try:
        employee_work_info_manager = instance.employee_work_info.reporting_manager_id
    except Exception:
        return HttpResponse("This Employee Dont Have any work information")
    return manager == employee_work_info_manager


class JobPositionView(APIView):
    serializer_class = JobPositionSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.view_jobposition"))
    def get(self, request, pk=None):
        company_id = _get_effective_company_id(request)
        if pk:
            job_position = object_check(JobPosition, pk)
            if job_position is None:
                return Response({"error": "Job position not found "}, status=404)
            if company_id is not None and not job_position.company_id.filter(pk=company_id).exists():
                return Response({"error": "Job position not found "}, status=404)
            serializer = self.serializer_class(job_position)
            return Response(serializer.data, status=200)

        job_positions = JobPosition.objects.all()
        if company_id is not None:
            job_positions = job_positions.filter(company_id=company_id)
        paginater = PageNumberPagination()
        page = paginater.paginate_queryset(job_positions, request)
        serializer = self.serializer_class(page, many=True)
        return paginater.get_paginated_response(serializer.data)

    @method_decorator(permission_required("base.change_jobposition"))
    def put(self, request, pk):
        job_position = object_check(JobPosition, pk)
        if job_position is None:
            return Response({"error": "Job position not found "}, status=404)
        serializer = self.serializer_class(job_position, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.add_jobposition"))
    def post(self, request):
        data = request.data.copy()
        # Auto-set company_id if not provided
        if "company_id" not in data or not data.get("company_id"):
            company_id = _get_effective_company_id(request)
            if company_id is not None:
                # Convert to list format for ManyToMany field
                data["company_id"] = [company_id]
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.delete_jobposition"))
    def delete(self, request, pk):
        job_position = object_check(JobPosition, pk)
        if job_position is None:
            return Response({"error": "Job position not found "}, status=404)
        response, status_code = object_delete(JobPosition, pk)
        return Response(response, status=status_code)


class DepartmentView(APIView):
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.view_department"), name="dispatch")
    def get(self, request, pk=None):
        company_id = _get_effective_company_id(request)
        if pk:
            department = object_check(Department, pk)
            if department is None:
                return Response({"error": "Department not found "}, status=404)
            if company_id is not None and not department.company_id.filter(pk=company_id).exists():
                return Response({"error": "Department not found "}, status=404)
            serializer = self.serializer_class(department)
            return Response(serializer.data, status=200)

        departments = Department.objects.all()
        if company_id is not None:
            departments = departments.filter(company_id=company_id)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(departments, request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @method_decorator(permission_required("base.change_department"), name="dispatch")
    def put(self, request, pk):
        department = object_check(Department, pk)
        if department is None:
            return Response({"error": "Department not found "}, status=404)
        serializer = self.serializer_class(department, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.add_department"), name="dispatch")
    def post(self, request):
        data = request.data.copy()
        # Auto-set company_id if not provided
        if "company_id" not in data or not data.get("company_id"):
            company_id = _get_effective_company_id(request)
            if company_id is not None:
                # Convert to list format for ManyToMany field
                data["company_id"] = [company_id]
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.delete_department"), name="dispatch")
    def delete(self, request, pk):
        department = object_check(Department, pk)
        if department is None:
            return Response({"error": "Department not found "}, status=404)
        response, status_code = object_delete(Department, pk)
        return Response(response, status=status_code)


class JobRoleView(APIView):
    serializer_class = JobRoleSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.view_jobrole"), name="dispatch")
    def get(self, request, pk=None):
        company_id = _get_effective_company_id(request)
        if pk:
            job_role = object_check(JobRole, pk)
            if job_role is None:
                return Response({"error": "Job role not found "}, status=404)
            if company_id is not None and not job_role.company_id.filter(pk=company_id).exists():
                return Response({"error": "Job role not found "}, status=404)
            serializer = self.serializer_class(job_role)
            return Response(serializer.data, status=200)

        job_roles = JobRole.objects.all()
        if company_id is not None:
            job_roles = job_roles.filter(company_id=company_id)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(job_roles, request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @method_decorator(permission_required("base.change_jobrole"), name="dispatch")
    def put(self, request, pk):
        job_role = object_check(JobRole, pk)
        if job_role is None:
            return Response({"error": "Job role not found "}, status=404)
        serializer = self.serializer_class(job_role, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.add_jobrole"), name="dispatch")
    def post(self, request):
        data = request.data.copy()
        # Auto-set company_id if not provided
        if "company_id" not in data or not data.get("company_id"):
            company_id = _get_effective_company_id(request)
            if company_id is not None:
                # Convert to list format for ManyToMany field
                data["company_id"] = [company_id]
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.delete_jobrole"), name="dispatch")
    def delete(self, request, pk):
        job_role = object_check(JobRole, pk)
        if job_role is None:
            return Response({"error": "Job role not found "}, status=404)
        response, status_code = object_delete(JobRole, pk)
        return Response(response, status=status_code)


class CompanyView(APIView):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.view_company"), name="dispatch")
    def get(self, request, pk=None):
        company_id = _get_effective_company_id(request)
        if pk:
            company = object_check(Company, pk)
            if company is None:
                return Response({"error": "Company not found "}, status=404)
            if company_id is not None and company.id != company_id:
                return Response({"error": "Company not found "}, status=404)
            serializer = self.serializer_class(company)
            return Response(serializer.data, status=200)

        companies = Company.objects.all()
        if company_id is not None:
            companies = companies.filter(id=company_id)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(companies, request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @method_decorator(permission_required("base.change_company"), name="dispatch")
    def put(self, request, pk):
        company = object_check(Company, pk)
        if company is None:
            return Response({"error": "Company not found "}, status=404)
        serializer = self.serializer_class(company, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.add_company"), name="dispatch")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.delete_company"), name="dispatch")
    def delete(self, request, pk):
        company = object_check(Company, pk)
        if company is None:
            return Response({"error": "Company not found "}, status=400)
        response, status_code = object_delete(Company, pk)
        return Response(response, status=status_code)


class MultipleApprovalConditionView(APIView):
    serializer_class = MultipleApprovalConditionSerializer
    permission_classes = [IsAuthenticated]

    def _get_queryset(self, request):
        queryset = MultipleApprovalCondition.objects.all().order_by("-department")
        company_id = request.query_params.get("company_id")
        if company_id and str(company_id).lower() != "all":
            queryset = queryset.filter(company_id=company_id)
        return queryset

    @method_decorator(permission_required("base.view_multipleapprovalcondition"), name="dispatch")
    def get(self, request, pk=None):
        if pk:
            condition = object_check(MultipleApprovalCondition, pk)
            if condition is None:
                return Response({"error": "Multiple approval condition not found"}, status=404)
            serializer = self.serializer_class(condition)
            return Response(serializer.data, status=200)

        queryset = self._get_queryset(request)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @method_decorator(permission_required("base.add_multipleapprovalcondition"), name="dispatch")
    def post(self, request):
        data = request.data.copy()
        approval_managers = data.pop("approval_managers", [])
        context = {"approval_managers": approval_managers}
        serializer = self.serializer_class(data=data, context=context)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.change_multipleapprovalcondition"), name="dispatch")
    def put(self, request, pk):
        condition = object_check(MultipleApprovalCondition, pk)
        if condition is None:
            return Response({"error": "Multiple approval condition not found"}, status=404)
        data = request.data.copy()
        approval_managers = data.pop("approval_managers", None)
        context = {"approval_managers": approval_managers}
        serializer = self.serializer_class(condition, data=data, context=context, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.delete_multipleapprovalcondition"), name="dispatch")
    def delete(self, request, pk):
        condition = object_check(MultipleApprovalCondition, pk)
        if condition is None:
            return Response({"error": "Multiple approval condition not found"}, status=404)
        response, status_code = object_delete(MultipleApprovalCondition, pk)
        return Response(response, status=status_code)


class MultipleApprovalConditionOptionsView(APIView):
    """Returns field and operator choices for multiple approval condition forms."""

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.view_multipleapprovalcondition"), name="dispatch")
    def get(self, request):
        return Response({
            "condition_fields": [{"value": v, "label": str(l)} for v, l in FIELD_CHOICE if v],
            "condition_operators": [{"value": v, "label": str(l)} for v, l in CONDITION_CHOICE],
        }, status=200)


class MailTemplateView(APIView):
    serializer_class = HorillaMailTemplateSerializer
    permission_classes = [IsAuthenticated]

    def _get_queryset(self, request):
        queryset = HorillaMailTemplate.objects.all().order_by("title")
        company_id = request.query_params.get("company_id")
        if company_id and str(company_id).lower() != "all":
            queryset = queryset.filter(company_id=company_id)
        return queryset

    @method_decorator(permission_required("base.view_horillamailtemplate"), name="dispatch")
    def get(self, request, pk=None):
        if pk:
            template = object_check(HorillaMailTemplate, pk)
            if template is None:
                return Response({"error": "Mail template not found"}, status=404)
            serializer = self.serializer_class(template)
            return Response(serializer.data, status=200)

        queryset = self._get_queryset(request)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @method_decorator(permission_required("base.add_horillamailtemplate"), name="dispatch")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.change_horillamailtemplate"), name="dispatch")
    def put(self, request, pk):
        template = object_check(HorillaMailTemplate, pk)
        if template is None:
            return Response({"error": "Mail template not found"}, status=404)
        serializer = self.serializer_class(template, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.delete_horillamailtemplate"), name="dispatch")
    def delete(self, request, pk):
        template = object_check(HorillaMailTemplate, pk)
        if template is None:
            return Response({"error": "Mail template not found"}, status=404)
        response, status_code = object_delete(HorillaMailTemplate, pk)
        return Response(response, status=status_code)


class MailTemplateDuplicateView(APIView):
    """Duplicate a mail template (creates copy with title suffixed by ' (copy)')."""

    serializer_class = HorillaMailTemplateSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.add_horillamailtemplate"), name="dispatch")
    def post(self, request, pk):
        template = object_check(HorillaMailTemplate, pk)
        if template is None:
            return Response({"error": "Mail template not found"}, status=404)
        new_template = HorillaMailTemplate.objects.create(
            title=f"{template.title} (copy)",
            body=template.body,
            company_id=template.company_id,
        )
        serializer = self.serializer_class(new_template)
        return Response(serializer.data, status=201)


class MailTemplateBulkDeleteView(APIView):
    """Bulk delete mail templates. Expects ?ids=1,2,3"""

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.delete_horillamailtemplate"), name="dispatch")
    def delete(self, request):
        ids_param = request.query_params.get("ids", "")
        ids = [int(x.strip()) for x in ids_param.split(",") if str(x).strip().isdigit()]
        if not ids:
            return Response({"error": "No valid ids provided"}, status=400)
        HorillaMailTemplate.objects.filter(id__in=ids).delete()
        return Response({"success": True, "deleted": len(ids)}, status=200)


class MailTemplateOptionsView(APIView):
    """Returns template language (placeholders for body editor autocomplete)."""

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.view_horillamailtemplate"), name="dispatch")
    def get(self, request):
        form = MailTemplateForm()
        mail_data = form.get_template_language()
        template_language = [
            {"label": str(label), "value": str(value)}
            for label, value in mail_data.items()
        ]
        return Response({"template_language": template_language}, status=200)


class WorkTypeView(APIView):
    serializer_class = WorkTypeSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        company_id = _get_effective_company_id(request)
        if pk:
            work_type = object_check(WorkType, pk)
            if work_type is None:
                return Response({"error": "WorkType not found"}, status=404)
            if company_id is not None and not work_type.company_id.filter(pk=company_id).exists():
                return Response({"error": "WorkType not found"}, status=404)
            serializer = self.serializer_class(work_type)
            return Response(serializer.data, status=200)

        work_types = WorkType.objects.all()
        if company_id is not None:
            work_types = work_types.filter(company_id=company_id)
        serializer = self.serializer_class(work_types, many=True)
        return Response(serializer.data)

    @method_decorator(permission_required("base.add_worktype"), name="dispatch")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.change_worktype"), name="dispatch")
    def put(self, request, pk):
        work_type = object_check(WorkType, pk)
        if work_type is None:
            return Response({"error": "WorkType not found"}, status=404)
        serializer = self.serializer_class(work_type, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.delete_worktype"), name="dispatch")
    def delete(self, request, pk):
        work_type = object_check(WorkType, pk)
        if work_type is None:
            return Response({"error": "WorkType not found"}, status=404)
        response, status_code = object_delete(WorkType, pk)
        return Response(response, status=status_code)


class WorkTypeRequestView(APIView):
    serializer_class = WorkTypeRequestSerializer
    filterset_class = WorkTypeRequestFilter
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        queryset = WorkTypeRequest.objects.all()
        user = request.user
        # checking user level permissions
        perm = "base.view_worktyperequest"
        queryset = permission_based_queryset(user, perm, queryset, user_obj=True)
        return queryset

    def get(self, request, pk=None):
        # individual object workflow
        if pk:
            work_type_request = object_check(WorkTypeRequest, pk)
            if work_type_request is None:
                return Response({"error": "WorkTypeRequest not found"}, status=404)
            serializer = self.serializer_class(work_type_request)
            return Response(serializer.data, status=200)
        # permission based queryset
        work_type_requests = self.get_queryset(request)
        # filtering queryset
        work_type_request_filter_queryset = self.filterset_class(
            request.GET, queryset=work_type_requests
        ).qs
        # groupby workflow
        field_name = request.GET.get("groupby_field", None)
        if field_name:
            url = request.build_absolute_uri()
            return groupby_queryset(
                request, url, field_name, work_type_request_filter_queryset
            )
        # pagination workflow
        paginater = PageNumberPagination()
        page = paginater.paginate_queryset(work_type_request_filter_queryset, request)
        serializer = self.serializer_class(page, many=True)
        return paginater.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            try:
                notify.send(
                    instance.employee_id,
                    recipient=(
                        instance.employee_id.employee_work_info.reporting_manager_id.employee_user_id
                    ),
                    verb=f"You have new work type request to \
                                validate for {instance.employee_id}",
                    verb_ar=f"لديك طلب نوع وظيفة جديد للتحقق من \
                                {instance.employee_id}",
                    verb_de=f"Sie haben eine neue Arbeitstypanfrage zur \
                                Validierung für {instance.employee_id}",
                    verb_es=f"Tiene una nueva solicitud de tipo de trabajo para \
                                validar para {instance.employee_id}",
                    verb_fr=f"Vous avez une nouvelle demande de type de travail\
                                à valider pour {instance.employee_id}",
                    icon="information",
                    redirect=f"/employee/work-type-request-view?id={instance.id}",
                    api_redirect=f"/api/base/worktype-requests/{instance.id}",
                )
            except Exception:
                pass
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @check_approval_status(WorkTypeRequest, "base.change_worktyperequest")
    @manager_or_owner_permission_required(
        WorkTypeRequest, "base.change_worktyperequest"
    )
    def put(self, request, pk):
        work_type_request = object_check(WorkTypeRequest, pk)
        if work_type_request is None:
            return Response({"error": "WorkTypeRequest not found"}, status=404)
        serializer = self.serializer_class(work_type_request, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)
    
    
    @check_approval_status(WorkTypeRequest, "base.change_worktyperequest")
    @manager_or_owner_permission_required(
        WorkTypeRequest, "base.delete_worktyperequest"
    )
    def delete(self, request, pk):
        work_type_request = object_check(WorkTypeRequest, pk)
        if work_type_request is None:
            return Response({"error": "WorkTypeRequest not found"}, status=404)
        response, status_code = object_delete(WorkTypeRequest, pk)
        return Response(response, status=status_code)


class WorkTypeRequestCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        work_type_request = WorkTypeRequest.find(pk)
        if (
            is_reportingmanger(request, work_type_request)
            or request.user.has_perm("base.cancel_worktyperequest")
            or work_type_request.employee_id == request.user.employee_get
            and work_type_request.approved == False
        ):
            work_type_request.canceled = True
            work_type_request.approved = False
            work_type_request.employee_id.employee_work_info.work_type_id = (
                work_type_request.previous_work_type_id
            )
            work_type_request.employee_id.employee_work_info.save()
            work_type_request.save()
            try:
                notify.send(
                    request.user.employee_get,
                    recipient=work_type_request.employee_id.employee_user_id,
                    verb="Your work type request has been rejected.",
                    verb_ar="تم إلغاء طلب نوع وظيفتك",
                    verb_de="Ihre Arbeitstypanfrage wurde storniert",
                    verb_es="Su solicitud de tipo de trabajo ha sido cancelada",
                    verb_fr="Votre demande de type de travail a été annulée",
                    redirect=f"/employee/work-type-request-view?id={work_type_request.id}",
                    icon="close",
                    api_redirect="/api/base/worktype-requests/<int:pk>/",
                )
            except:
                pass
        return Response(status=200)


class WorkRequestApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        work_type_request = WorkTypeRequest.find(pk)
        if (
            is_reportingmanger(request, work_type_request)
            or request.user.has_perm("approve_worktyperequest")
            or request.user.has_perm("change_worktyperequest")
            and not work_type_request.approved
        ):
            """
            Here the request will be approved, can send mail right here
            """
            if not work_type_request.is_any_work_type_request_exists():
                work_type_request.approved = True
                work_type_request.canceled = False
                work_type_request.save()
                try:
                    notify.send(
                        request.user.employee_get,
                        recipient=work_type_request.employee_id.employee_user_id,
                        verb="Your work type request has been approved.",
                        verb_ar="تمت الموافقة على طلب نوع وظيفتك.",
                        verb_de="Ihre Arbeitstypanfrage wurde genehmigt.",
                        verb_es="Su solicitud de tipo de trabajo ha sido aprobada.",
                        verb_fr="Votre demande de type de travail a été approuvée.",
                        redirect=f"/employee/work-type-request-view?id={work_type_request.id}",
                        icon="checkmark",
                        api_redirect="/api/base/worktype-requests/<int:pk>/",
                    )
                except Exception:
                    pass
                return Response({"status": "approved"})
        else:
            return Response({"error": "You don't have permission"}, status=400)


class WorkTypeRequestExport(APIView):
    permission_classes = [IsAuthenticated]

    @manager_permission_required("base.view_worktyperequest")
    def get(self, request):
        return work_type_request_export(request)


class IndividualRotatingWorktypesView(APIView):
    serializer_class = RotatingWorkTypeAssignSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if individual_permssion_check(request) == False:
            return Response({"error": "you have no permssion to view"}, status=400)
        if pk:
            rotating_work_type_assign = object_check(RotatingWorkTypeAssign, pk)
            if rotating_work_type_assign is None:
                return Response(
                    {"error": "RotatingWorkTypeAssign not found"}, status=404
                )
            serializer = self.serializer_class(rotating_work_type_assign)
            return Response(serializer.data, status=200)
        employee_id = request.GET.get("employee_id", None)
        rotating_work_type_assigns = RotatingWorkTypeAssign.objects.filter(
            employee_id=employee_id
        )
        pagenation = PageNumberPagination()
        page = pagenation.paginate_queryset(rotating_work_type_assigns, request)
        serializer = self.serializer_class(page, many=True)
        return pagenation.get_paginated_response(serializer.data)


class RotatingWorkTypeAssignView(APIView):
    serializer_class = RotatingWorkTypeAssignSerializer
    filterset_class = RotatingWorkTypeAssignFilter
    permission_classes = [IsAuthenticated]

    def _permission_check(self, request, obj=None, pk=None):
        if pk:
            employee = request.user.employee_get
            manager = obj.employee_id.get_reporting_manager()
            if (
                employee == obj.employee_id
                or manager == employee
                or request.user.has_perm("base.view_rotatingworktypeassign")
            ):
                return True
            return False

    @manager_permission_required("base.view_rotatingworktypeassign")
    def get(self, request, pk=None):

        if pk:

            rotating_work_type_assign = object_check(RotatingWorkTypeAssign, pk)
            if rotating_work_type_assign is None:
                return Response(
                    {"error": "RotatingWorkTypeAssign not found"}, status=404
                )
            serializer = self.serializer_class(rotating_work_type_assign)
            return Response(serializer.data, status=200)
        rotating_work_type_assigns = RotatingWorkTypeAssign.objects.all()
        rotating_work_type_assigns_filter_queryset = self.filterset_class(
            request.GET, queryset=rotating_work_type_assigns
        ).qs
        field_name = request.GET.get("groupby_field", None)
        if field_name:
            # groupby workflow
            url = request.build_absolute_uri()
            return groupby_queryset(
                request, url, field_name, rotating_work_type_assigns_filter_queryset
            )

        pagenation = PageNumberPagination()
        page = pagenation.paginate_queryset(
            rotating_work_type_assigns_filter_queryset, request
        )
        serializer = self.serializer_class(page, many=True)
        return pagenation.get_paginated_response(serializer.data)

    @manager_permission_required("base.add_rotatingworktypeassign")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            try:
                users = [employee.employee_user_id for employee in obj]
                notify.send(
                    request.user.employee_get,
                    recipient=users,
                    verb="You are added to rotating work type",
                    verb_ar="تمت إضافتك إلى نوع العمل المتناوب",
                    verb_de="Sie werden zum rotierenden Arbeitstyp hinzugefügt",
                    verb_es="Se le agrega al tipo de trabajo rotativo",
                    verb_fr="Vous êtes ajouté au type de travail rotatif",
                    icon="infinite",
                    redirect="/employee/employee-profile/",
                    api_redirect="",
                )
            except:
                pass
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @manager_permission_required("base.change_rotatingworktypeassign")
    def put(self, request, pk):
        rotating_work_type_assign = object_check(RotatingWorkTypeAssign, pk)
        if rotating_work_type_assign is None:
            return Response({"error": "RotatingWorkTypeAssign not found"}, status=404)
        serializer = self.serializer_class(rotating_work_type_assign, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @manager_permission_required("base.delete_rotatingworktypeassign")
    def delete(self, request, pk):
        rotating_work_type_assign = object_check(RotatingWorkTypeAssign, pk)
        if rotating_work_type_assign is None:
            return Response({"error": "RotatingWorkTypeAssign not found"}, status=404)
        response, status_code = object_delete(RotatingWorkTypeAssign, pk)
        return Response(response, status=status_code)


class IndividualWorkTypeRequestView(APIView):
    serializer_class = WorkTypeRequestSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if individual_permssion_check(request) == False:
            return Response({"error": "you have no permssion to view"}, status=400)

        # individual object workflow
        if pk:
            work_type_request = object_check(WorkTypeRequest, pk)
            if work_type_request is None:
                return Response({"error": "WorkTypeRequest not found"}, status=404)
            serializer = self.serializer_class(work_type_request)
            return Response(serializer.data, status=200)
        employee_id = request.GET.get("employee_id", None)
        work_type_request = WorkTypeRequest.objects.filter(employee_id=employee_id)
        paginater = PageNumberPagination()
        page = paginater.paginate_queryset(work_type_request, request)
        serializer = self.serializer_class(page, many=True)
        return paginater.get_paginated_response(serializer.data)


class EmployeeShiftDayView(APIView):
    """List EmployeeShiftDay (Monday, Tuesday, etc.) for filters."""

    serializer_class = EmployeeShiftDaySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = EmployeeShiftDay.objects.all().order_by("id")
        serializer = self.serializer_class(days, many=True)
        return Response(serializer.data, status=200)


class EmployeeShiftView(APIView):
    serializer_class = EmployeeShiftSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        company_id = _get_effective_company_id(request)
        if pk:
            employee_shift = object_check(EmployeeShift, pk)
            if employee_shift is None:
                return Response({"error": "EmployeeShift not found"}, status=404)
            if company_id is not None and not employee_shift.company_id.filter(pk=company_id).exists():
                return Response({"error": "EmployeeShift not found"}, status=404)
            serializer = self.serializer_class(employee_shift)
            return Response(serializer.data, status=200)

        employee_shifts = EmployeeShift.objects.all()
        if company_id is not None:
            employee_shifts = employee_shifts.filter(company_id=company_id)
        serializer = self.serializer_class(employee_shifts, many=True)
        return Response(serializer.data, status=200)

    @method_decorator(permission_required("base.add_employeeshift"), name="dispatch")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.change_employeeshift"), name="dispatch")
    def put(self, request, pk):
        employee_shift = object_check(EmployeeShift, pk)
        if employee_shift is None:
            return Response({"error": "EmployeeShift not found"}, status=404)
        serializer = self.serializer_class(employee_shift, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.delete_employeeshift"), name="dispatch")
    def delete(self, request, pk):
        employee_shift = object_check(EmployeeShift, pk)
        if employee_shift is None:
            return Response({"error": "EmployeeShift not found"}, status=404)
        response, status_code = object_delete(EmployeeShift, pk)
        return Response(response, status=status_code)


class EmployeeShiftScheduleView(APIView):
    serializer_class = EmployeeShiftScheduleSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(
        permission_required("base.view_employeeshiftschedule"), name="dispatch"
    )
    def get(self, request, pk=None):
        if pk:
            employee_shift_schedule = object_check(EmployeeShiftSchedule, pk)
            if employee_shift_schedule is None:
                return Response(
                    {"error": "EmployeeShiftSchedule not found"}, status=404
                )
            serializer = self.serializer_class(employee_shift_schedule)
            return Response(serializer.data, status=200)

        employee_shift_schedules = EmployeeShiftSchedule.objects.all()
        serializer = self.serializer_class(employee_shift_schedules, many=True)
        return Response(serializer.data, status=200)

    @method_decorator(
        permission_required("base.add_employeeshiftschedule"), name="dispatch"
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @method_decorator(
        permission_required("base.change_employeeshiftschedule"), name="dispatch"
    )
    def put(self, request, pk):
        employee_shift_schedule = object_check(EmployeeShiftSchedule, pk)
        if employee_shift_schedule is None:
            return Response({"error": "EmployeeShiftSchedule not found"}, status=404)
        serializer = self.serializer_class(employee_shift_schedule, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(
        permission_required("base.delete_employeeshiftschedule"), name="dispatch"
    )
    def delete(self, request, pk):
        employee_shift_schedule = object_check(EmployeeShiftSchedule, pk)
        if employee_shift_schedule is None:
            return Response({"error": "EmployeeShiftSchedule not found"}, status=404)
        response, status_code = object_delete(EmployeeShiftSchedule, pk)
        return Response(response, status=status_code)


class RotatingShiftView(APIView):
    serializer_class = RotatingShiftSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.view_rotatingshift"), name="dispatch")
    def get(self, request, pk=None):

        if pk:
            rotating_shift = object_check(RotatingShift, pk)
            if rotating_shift is None:
                return Response({"error": "RotatingShift not found"}, status=404)
            serializer = self.serializer_class(rotating_shift)
            return Response(serializer.data, status=200)

        employee_id = request.GET.get(
            "employee_id"
        )  # Get the employee_id from query parameters
        if employee_id:  # Check if employee_ids are present in the request
            rotating_shifts = RotatingShift.objects.filter(
                employee_id__in=[employee_id]
            )

        rotating_shifts = RotatingShift.objects.all()
        serializer = self.serializer_class(rotating_shifts, many=True)
        return Response(serializer.data, status=200)

    @method_decorator(permission_required("base.add_rotatingshift"), name="dispatch")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.change_rotatingshift"), name="dispatch")
    def put(self, request, pk):
        rotating_shift = object_check(RotatingShift, pk)
        if rotating_shift is None:
            return Response({"error": "RotatingShift not found"}, status=404)
        serializer = self.serializer_class(rotating_shift, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.delete_rotatingshift"), name="dispatch")
    def delete(self, request, pk):
        rotating_shift = object_check(RotatingShift, pk)
        if rotating_shift is None:
            return Response({"error": "RotatingShift not found"}, status=404)
        response, status_code = object_delete(RotatingShift, pk)
        return Response(response, status=status_code)


class IndividualRotatingShiftView(APIView):
    serializer_class = RotatingShiftAssignSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if individual_permssion_check(request) == False:
            return Response({"error": "you have no permssion to view"}, status=400)

        if pk:
            rotating_shift_assign = object_check(RotatingShiftAssign, pk)
            if rotating_shift_assign is None:
                return Response({"error": "RotatingShiftAssign not found"}, status=404)
            serializer = self.serializer_class(rotating_shift_assign)
            return Response(serializer.data, status=200)
        employee_id = request.GET.get("employee_id", None)
        rotating_shift_assigns = RotatingShiftAssign.objects.filter(
            employee_id=employee_id
        )

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(rotating_shift_assigns, request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class RotatingShiftAssignView(APIView):
    serializer_class = RotatingShiftAssignSerializer
    filterset_class = RotatingShiftAssignFilters
    permission_classes = [IsAuthenticated]

    @manager_permission_required("base.view_rotatingshiftassign")
    def get(self, request, pk=None):
        if pk:
            rotating_shift_assign = object_check(RotatingShiftAssign, pk)
            if rotating_shift_assign is None:
                return Response({"error": "RotatingShiftAssign not found"}, status=404)
            serializer = self.serializer_class(rotating_shift_assign)
            return Response(serializer.data, status=200)

        rotating_shift_assigns = RotatingShiftAssign.objects.all()
        rotating_shift_assigns_filter_queryset = self.filterset_class(
            request.GET, queryset=rotating_shift_assigns
        ).qs
        field_name = request.GET.get("groupby_field", None)
        if field_name:
            # groupby workflow
            url = request.build_absolute_uri()
            return groupby_queryset(
                request, url, field_name, rotating_shift_assigns_filter_queryset
            )

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(
            rotating_shift_assigns_filter_queryset, request
        )
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @manager_permission_required("base.add_rotatingshiftassign")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @manager_permission_required("base.change_rotatingshiftassign")
    def put(self, request, pk):
        rotating_shift_assign = object_check(RotatingShiftAssign, pk)
        if rotating_shift_assign is None:
            return Response({"error": "RotatingShiftAssign not found"}, status=404)
        serializer = self.serializer_class(rotating_shift_assign, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @manager_permission_required("base.delete_rotatingshiftassign")
    def delete(self, request, pk):
        rotating_shift_assign = object_check(RotatingShiftAssign, pk)
        if rotating_shift_assign is None:
            return Response({"error": "RotatingShiftAssign not found"}, status=404)
        response, status_code = object_delete(RotatingShiftAssign, pk)
        return Response(response, status=status_code)


class IndividualShiftRequestView(APIView):
    serializer_class = ShiftRequestSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if individual_permssion_check(request) == False:
            return Response({"error": "you have no permssion to view"}, status=400)

        if pk:
            shift_request = object_check(ShiftRequest, pk)
            if shift_request is None:
                return Response({"error": "EmployeeShift not found"}, status=404)
            serializer = self.serializer_class(shift_request)
            return Response(serializer.data, status=200)
        employee_id = request.GET.get("employee_id", None)
        shift_requests = ShiftRequest.objects.filter(employee_id=employee_id)
        paginater = PageNumberPagination()
        page = paginater.paginate_queryset(shift_requests, request)
        serializer = self.serializer_class(page, many=True)
        return paginater.get_paginated_response(serializer.data)


class ShiftRequestView(APIView):
    serializer_class = ShiftRequestSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ShiftRequestFilter
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        queryset = ShiftRequest.objects.all()
        user = request.user
        # checking user level permissions
        perm = "base.view_shiftrequest"
        queryset = permission_based_queryset(user, perm, queryset, user_obj=True)
        return queryset

    def get(self, request, pk=None):
        # individual section
        if pk:
            shift_request = object_check(ShiftRequest, pk)
            if shift_request is None:
                return Response({"error": "ShiftRequest not found"}, status=404)
            serializer = self.serializer_class(shift_request)
            return Response(serializer.data, status=200)
        # filter section
        shift_requests = self.get_queryset(request)
        shift_requests_filter_queryset = self.filterset_class(
            request.GET, queryset=shift_requests
        ).qs
        # groupby section
        field_name = request.GET.get("groupby_field", None)
        if field_name:
            url = request.build_absolute_uri()
            return groupby_queryset(
                request, url, field_name, shift_requests_filter_queryset
            )
        # pagination section
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(shift_requests_filter_queryset, request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        if hasattr(request.user, 'employee_get') and request.user.employee_get:
          data['employee_id'] = request.user.employee_get.id

        serializer = self.serializer_class(data=data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @check_approval_status(ShiftRequest, "base.change_shiftrequest")
    @manager_or_owner_permission_required(ShiftRequest, "base.change_shiftrequest")
    def put(self, request, pk):
        shift_request = object_check(ShiftRequest, pk)
        if shift_request is None:
            return Response({"error": "ShiftRequest not found"}, status=404)
        serializer = self.serializer_class(shift_request, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @check_approval_status(ShiftRequest, "base.delete_shiftrequest")
    @manager_or_owner_permission_required(ShiftRequest, "base.delete_shiftrequest")
    def delete(self, request, pk):
        shift_request = object_check(ShiftRequest, pk)
        if shift_request is None:
            return Response({"error": "ShiftRequest not found"}, status=404)
        response, status_code = object_delete(ShiftRequest, pk)
        return Response(response, status=status_code)


class RotatingWorkTypeView(APIView):
    serializer_class = RotatingWorkTypeSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.view_rotatingworktype"))
    def get(self, request, pk=None):
        if pk:
            rotating_work_type = object_check(RotatingWorkType, pk)
            if rotating_work_type is None:
                return Response({"error": "RotatingWorkType not found"}, status=404)
            serializer = self.serializer_class(rotating_work_type)
            return Response(serializer.data, status=200)

        rotating_work_types = RotatingWorkType.objects.all()
        serializer = self.serializer_class(rotating_work_types, many=True)
        return Response(serializer.data, status=200)

    @method_decorator(permission_required("base.add_rotatingworktype"), name="dispatch")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @method_decorator(
        permission_required("base.change_rotatingworktype"), name="dispatch"
    )
    def put(self, request, pk):
        rotating_work_type = object_check(RotatingWorkType, pk)
        if rotating_work_type is None:
            return Response({"error": "RotatingWorkType not found"}, status=404)
        serializer = self.serializer_class(rotating_work_type, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(
        permission_required("base.delete_rotatingworktype"), name="dispatch"
    )
    def delete(self, request, pk):
        rotating_work_type = object_check(RotatingWorkType, pk)
        if rotating_work_type is None:
            return Response({"error": "RotatingWorkType not found"}, status=404)
        response, status_code = object_delete(RotatingWorkType, pk)
        return Response(response, status=status_code)


class ShiftRequestApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        shift_request = ShiftRequest.objects.get(id=pk)
        if (
            is_reportingmanger(request, shift_request)
            or request.user.has_perm("approve_shiftrequest")
            or request.user.has_perm("change_shiftrequest")
            and not shift_request.approved
        ):
            """
            here the request will be approved, can send mail right here
            """
            if not shift_request.is_any_request_exists():
                shift_request.approved = True
                shift_request.canceled = False
                shift_request.save()
                return Response({"status": "success"}, status=200)
            else:
                return Response(
                    {"error": "Already request exits on same date"}, status=400
                )

        return Response({"error": "No permission "}, status=400)


class ShiftRequestBulkApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ids = request.data["ids"]
        length = len(ids)
        count = 0
        for id in ids:
            shift_request = ShiftRequest.objects.get(id=id)
            if (
                is_reportingmanger(request, shift_request)
                or request.user.has_perm("approve_shiftrequest")
                or request.user.has_perm("change_shiftrequest")
                and not shift_request.approved
            ):
                """
                here the request will be approved, can send mail right here
                """
                shift_request.approved = True
                shift_request.canceled = False
                employee_work_info = shift_request.employee_id.employee_work_info
                employee_work_info.shift_id = shift_request.shift_id
                employee_work_info.save()
                shift_request.save()
                count += 1
        if length == count:
            return Response({"status": "success"}, status=200)
        return Response({"status": "failed"}, status=400)


class ShiftRequestCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        shift_request = ShiftRequest.objects.get(id=pk)
        if (
            is_reportingmanger(request, shift_request)
            or request.user.has_perm("base.cancel_shiftrequest")
            or shift_request.employee_id == request.user.employee_get
            and shift_request.approved == False
        ):
            shift_request.canceled = True
            shift_request.approved = False
            shift_request.employee_id.employee_work_info.shift_id = (
                shift_request.previous_shift_id
            )
            shift_request.employee_id.employee_work_info.save()
            shift_request.save()
            return Response({"status": "success"}, status=200)
        return Response({"status": "failed"}, status=400)


class ShiftRequestBulkCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ids = request.data.get("ids", None)
        length = len(ids)
        count = 0
        for id in ids:
            shift_request = ShiftRequest.objects.get(id=id)
            if (
                is_reportingmanger(request, shift_request)
                or request.user.has_perm("base.cancel_shiftrequest")
                or shift_request.employee_id == request.user.employee_get
                and shift_request.approved == False
            ):
                shift_request.canceled = True
                shift_request.approved = False
                shift_request.employee_id.employee_work_info.shift_id = (
                    shift_request.previous_shift_id
                )
                shift_request.employee_id.employee_work_info.save()
                shift_request.save()
                count += 1
        if length == count:
            return Response({"status": "success"}, status=200)
        return Response({"status": "failed"}, status=400)


class ShiftRequestDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk=None):

        if pk is None:
            try:
                ids = request.data["ids"]
                shift_requests = ShiftRequest.objects.filter(id__in=ids)
                shift_requests.delete()
            except Exception as e:
                return Response({"status": "failed", "error": str(e)}, status=400)
            return Response({"status": "success"}, status=200)
        try:
            shift_request = ShiftRequest.objects.get(id=pk)
            if not shift_request.approved:
                return Response(
                    {"status": "failed", "error": "Cannot delete shift request that is not approved."},
                    status=400,
                )
            shift_request.delete()

        except ShiftRequest.DoesNotExist:
            return Response(
                {"status": "failed", "error": "Shift request does not exists"},
                status=400,
            )
        return Response({"status": "deleted"}, status=200)


class ShiftRequestExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return shift_request_export(request)


class ShiftRequestAllocationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        shift_request = ShiftRequest.objects.get(id=id)
        if not shift_request.is_any_request_exists():
            shift_request.reallocate_approved = True
            shift_request.reallocate_canceled = False
            shift_request.save()
            return Response({"status": "success"}, status=200)
        return Response({"status": "failed"}, status=400)


class RotatingShiftAssignExport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from base.views import rotating_shift_assign_export
        return rotating_shift_assign_export(request)


class RotatingWorkTypeAssignExport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return rotating_work_type_assign_export(request)


class RotatingWorkTypeAssignBulkArchive(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, status):
        ids = request.data.get("ids", None)
        try:
            rotating_work_type_assigns = RotatingWorkTypeAssign.objects.filter(id__in=ids)
            is_active = str(status).lower() == "true"
            rotating_work_type_assigns.update(is_active=is_active)
            return Response({"status": "success"}, status=200)
        except Exception as E:
            return Response({"error": str(E)}, status=400)


class RotatingWorkTypeAssignBulkDelete(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        ids = request.data.get("ids", None)
        try:
            rotating_work_type_assigns = RotatingWorkTypeAssign.objects.filter(id__in=ids)
            rotating_work_type_assigns.delete()
            return Response({"status": "success"}, status=200)
        except Exception as E:
            return Response({"error": str(E)}, status=400)


class RotatingShiftAssignBulkArchive(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, status):
        ids = request.data.get("ids", None)
        try:
            rotating_shift_asssign = RotatingShiftAssign.objects.filter(id__in=ids)
            rotating_shift_asssign.update(is_active=status)
            return Response({"status": "success"}, status=200)
        except Exception as E:
            return Response({"error": str(E)}, status=400)


class RotatingShiftAssignBulkDelete(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        ids = request.data.get("ids", None)
        try:
            rotating_shift_asssign = RotatingShiftAssign.objects.filter(id__in=ids)
            rotating_shift_asssign.delete()
            return Response({"status": "success"}, status=200)
        except Exception as E:
            return Response({"error": str(E)}, status=400)


class RotatingWorKTypePermissionCheck(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        manager = Employee.objects.filter(id=id).first().get_reporting_manager()
        if (
            request.user.has_perm("base.add_rotatingworktypeassign")
            or request.user.employee_get == manager
        ):
            return Response(status=200)
        return Response(status=400)


class RotatingShiftPermissionCheck(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        manager = Employee.objects.filter(id=id).first().get_reporting_manager()
        if (
            request.user.has_perm("base.add_rotatingshiftassign")
            or request.user.employee_get == manager
        ):
            return Response(status=200)
        return Response(status=400)


class WorktypeRequestApprovePermissionCheck(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        instance = Employee.objects.filter(id=request.GET.get("employee_id")).first()
        if (
            _is_reportingmanger(request, instance)
            or request.user.has_perm("approve_shiftrequest")
            or request.user.has_perm("change_shiftrequest")
        ):
            return Response(status=200)
        return Response(status=400)


class ShiftRequestApprovePermissionCheck(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        instance = Employee.objects.filter(id=request.GET.get("employee_id")).first()
        if (
            _is_reportingmanger(request, instance)
            or request.user.has_perm("approve_shiftrequest")
            or request.user.has_perm("change_shiftrequest")
        ):
            return Response(status=200)
        return Response(status=400)


class EmployeeTabPermissionCheck(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        instance = Employee.objects.filter(id=request.GET.get("employee_id")).first()
        if _is_reportingmanger(request, instance) or request.user.has_perms(
            [
                "view.view_worktyperequest",
                "attendance.view_shiftrequest",
                "employee.change_employee",
            ]
        ):
            return Response(status=200)
        return Response({"message": "No permission"}, status=400)


class CheckUserLevel(APIView):

    def get(self, request):
        perm = request.GET.get("perm")
        if request.user.has_perm(perm):
            return Response(status=200)
        return Response({"error": "No permission"}, status=400)


class BiometricAttendanceAPIView(APIView):
    """
    GET: Return current biometric attendance setting (single instance, create if none).
    PATCH: Update is_installed (activate/deactivate biometric attendance).
    Matches backend UI: /settings/activate-biometric-attendance and enable_biometric_attendance_view.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BiometricAttendanceSerializer

    @method_decorator(permission_required("base.view_biometricattendance"))
    def get(self, request):
        instance = BiometricAttendance.objects.first()
        if not instance:
            instance = BiometricAttendance.objects.create(is_installed=False)
        serializer = self.serializer_class(instance)
        return Response(serializer.data, status=200)

    @method_decorator(permission_required("base.change_biometricattendance"))
    def patch(self, request):
        instance = BiometricAttendance.objects.first()
        if not instance:
            instance = BiometricAttendance.objects.create(is_installed=False)
        is_installed = request.data.get("is_installed")
        if is_installed is not None:
            instance.is_installed = bool(is_installed)
            instance.save()
        serializer = self.serializer_class(instance)
        return Response(serializer.data, status=200)


class AttendanceAllowedIPAPIView(APIView):
    """
    GET: Return current IP restriction setting and allowed IP list.
    PATCH: Update is_enabled and/or full allowed_ips list.
    Mirrors backend IP Restriction UI behavior.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = AttendanceAllowedIPSerializer

    @method_decorator(permission_required("attendance.add_attendance"))
    def get(self, request):
        instance = AttendanceAllowedIP.objects.first()
        if not instance:
            instance = AttendanceAllowedIP.objects.create(
                is_enabled=False, additional_data={"allowed_ips": []}
            )
        serializer = self.serializer_class(instance)
        return Response(serializer.data, status=200)

    @method_decorator(permission_required("attendance.change_attendance"))
    def patch(self, request):
        instance = AttendanceAllowedIP.objects.first()
        if not instance:
            instance = AttendanceAllowedIP.objects.create(
                is_enabled=False, additional_data={"allowed_ips": []}
            )
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


class BiometricDevicesAPIView(APIView):
    """
    CRUD for BiometricDevices.
    GET list: paginated devices (requires biometric.view_biometricdevices).
    GET detail: single device by UUID.
    POST: create device (requires biometric.add_biometricdevices).
    PUT/PATCH: update device (requires biometric.change_biometricdevices).
    DELETE: delete device (requires biometric.delete_biometricdevices).
    """

    permission_classes = [IsAuthenticated]
    serializer_class = BiometricDeviceSerializer

    def get_queryset(self):
        from biometric.models import BiometricDevices

        return BiometricDevices.objects.all().order_by("-created_at")

    @method_decorator(permission_required("biometric.view_biometricdevices"))
    def get(self, request, pk=None):
        from biometric.models import BiometricDevices

        queryset = self.get_queryset()
        if pk:
            try:
                device = queryset.get(id=pk)
            except (ValueError, BiometricDevices.DoesNotExist):
                return Response({"detail": "Device not found."}, status=404)
            serializer = self.serializer_class(device)
            return Response(serializer.data, status=200)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @method_decorator(permission_required("biometric.add_biometricdevices"))
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=201)
            except Exception as e:
                return Response(
                    {"error": str(e) if hasattr(e, "message") else "Validation failed"},
                    status=400,
                )
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("biometric.change_biometricdevices"))
    def put(self, request, pk):
        from biometric.models import BiometricDevices

        try:
            device = self.get_queryset().get(id=pk)
        except (ValueError, BiometricDevices.DoesNotExist):
            return Response({"detail": "Device not found."}, status=404)
        serializer = self.serializer_class(device, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=200)
            except Exception as e:
                return Response(
                    {"error": str(e) if hasattr(e, "message") else "Validation failed"},
                    status=400,
                )
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("biometric.change_biometricdevices"))
    def patch(self, request, pk):
        from biometric.models import BiometricDevices

        try:
            device = self.get_queryset().get(id=pk)
        except (ValueError, BiometricDevices.DoesNotExist):
            return Response({"detail": "Device not found."}, status=404)
        serializer = self.serializer_class(device, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=200)
            except Exception as e:
                return Response(
                    {"error": str(e) if hasattr(e, "message") else "Validation failed"},
                    status=400,
                )
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("biometric.delete_biometricdevices"))
    def delete(self, request, pk):
        from biometric.models import BiometricDevices

        try:
            device = self.get_queryset().get(id=pk)
            device.delete()
            return Response(status=204)
        except (ValueError, BiometricDevices.DoesNotExist):
            return Response({"detail": "Device not found."}, status=404)


class GeneralSettingsAPIView(APIView):
    """
    GET: Return announcement expire days, history tracking settings, and tracking field choices.
    PUT/PATCH: Update announcement_expire_days and/or history tracking (tracking_fields, work_info_track).
    """

    permission_classes = [IsAuthenticated]

    # Same exclusions as horilla_audit.forms.HistoryTrackingFieldsForm
    TRACKING_EXCLUDED_FIELDS = [
        "id",
        "employee_id",
        "objects",
        "mobile",
        "contract_end_date",
        "additional_info",
        "is_from_onboarding",
        "is_directly_converted",
        "experience",
    ]

    def _get_tracking_field_choices(self):
        from employee.models import EmployeeWorkInformation as model

        return [
            {"value": field.name, "label": str(field.verbose_name)}
            for field in model._meta.get_fields()
            if getattr(field, "verbose_name", None) is not None
            and field.name not in self.TRACKING_EXCLUDED_FIELDS
        ]

    def get(self, request):
        from base.models import AnnouncementExpire, DynamicPagination
        from horilla_audit.models import HistoryTrackingFields
        from django.apps import apps
        from horilla.methods import get_horilla_model_class

        expire = AnnouncementExpire.objects.first()
        announcement_expire_days = expire.days if expire else 30

        history = HistoryTrackingFields.objects.first()
        tracking_fields = []
        work_info_track = True
        if history and history.tracking_fields and isinstance(history.tracking_fields, dict):
            tracking_fields = list(history.tracking_fields.get("tracking_fields") or [])
        if history:
            work_info_track = history.work_info_track

        # Default Records Per Page (Pagination)
        pagination = DynamicPagination.objects.filter(user_id=request.user).first()
        pagination_value = pagination.pagination if pagination else 50

        # Employee Account Restrictions
        from horilla_audit.models import AccountBlockUnblock
        from employee.models import ProfileEditFeature
        enabled_block_unblock = (
            AccountBlockUnblock.objects.exists()
            and AccountBlockUnblock.objects.first().is_enabled
        )
        enabled_profile_edit = (
            ProfileEditFeature.objects.exists()
            and ProfileEditFeature.objects.first().is_enabled
        )

        # Badge Prefix
        from employee.models import EmployeeGeneralSetting
        prefix_instance = EmployeeGeneralSetting.objects.first()
        badge_prefix = prefix_instance.badge_id_prefix if prefix_instance else ""
        badge_prefix_company_id = prefix_instance.company_id.id if prefix_instance and prefix_instance.company_id else None

        # Encashment Redeem Condition (if payroll installed)
        bonus_unit = None
        leave_unit = None
        if apps.is_installed("payroll"):
            EncashmentGeneralSettings = get_horilla_model_class(
                app_label="payroll", model="encashmentgeneralsettings"
            )
            encashment = EncashmentGeneralSettings.objects.first()
            if encashment:
                bonus_unit = encashment.bonus_amount
                leave_unit = encashment.leave_amount

        # Currency (if payroll installed)
        currency_symbol = None
        currency_position = None
        currency_company_id = None
        if apps.is_installed("payroll"):
            PayrollSettings = get_horilla_model_class(
                app_label="payroll", model="payrollsettings"
            )
            currency = PayrollSettings.objects.first()
            if currency:
                currency_symbol = currency.currency_symbol
                currency_position = currency.position
                currency_company_id = currency.company_id.id if currency.company_id else None

        # Resignation Request (if offboarding installed)
        enabled_resignation_request = False
        if apps.is_installed("offboarding"):
            OffboardingGeneralSetting = get_horilla_model_class(
                app_label="offboarding", model="offboardinggeneralsetting"
            )
            offboarding = OffboardingGeneralSetting.objects.first()
            if offboarding:
                enabled_resignation_request = offboarding.resignation_request

        # Notice Period (if payroll installed - stored in PayrollGeneralSetting)
        notice_period_days = None
        if apps.is_installed("payroll"):
            PayrollGeneralSetting = get_horilla_model_class(
                app_label="payroll", model="payrollgeneralsetting"
            )
            payroll_gen = PayrollGeneralSetting.objects.first()
            if payroll_gen:
                notice_period_days = getattr(payroll_gen, "notice_period", None)

        # Time Runner / At-Work Tracker (if attendance installed)
        enabled_timerunner = False
        if apps.is_installed("attendance"):
            AttendanceGeneralSetting = get_horilla_model_class(
                app_label="attendance", model="attendancegeneralsetting"
            )
            attendance = AttendanceGeneralSetting.objects.first()
            if attendance:
                enabled_timerunner = attendance.time_runner

        return Response(
            {
                "announcement_expire_days": announcement_expire_days,
                "history_tracking": {
                    "tracking_fields": tracking_fields,
                    "work_info_track": work_info_track,
                },
                "tracking_field_choices": self._get_tracking_field_choices(),
                "pagination": pagination_value,
                "restrict_login_account": enabled_block_unblock,
                "restrict_profile_edit": enabled_profile_edit,
                "badge_prefix": badge_prefix,
                "badge_prefix_company_id": badge_prefix_company_id,
                "bonus_unit": bonus_unit,
                "leave_unit": leave_unit,
                "currency_symbol": currency_symbol,
                "currency_position": currency_position,
                "currency_company_id": currency_company_id,
                "resignation_request": enabled_resignation_request,
                "time_runner": enabled_timerunner,
                "notice_period_days": notice_period_days,
            },
            status=200,
        )

    def put(self, request):
        return self._update(request)

    def patch(self, request):
        return self._update(request)

    def _update(self, request):
        from base.models import AnnouncementExpire
        from horilla_audit.models import HistoryTrackingFields

        data = request.data
        updated = {}

        if "announcement_expire_days" in data:
            if not request.user.has_perm("base.change_announcementexpire"):
                return Response(
                    {"error": "Permission denied: change announcement expire"},
                    status=403,
                )
            expire = AnnouncementExpire.objects.first()
            if not expire:
                expire = AnnouncementExpire.objects.create(days=30)
            days = data.get("announcement_expire_days")
            if days is not None:
                expire.days = int(days)
                expire.save()
                updated["announcement_expire_days"] = expire.days

        if "tracking_fields" in data or "work_info_track" in data:
            if not request.user.has_perm("horilla_audit.view_historytrackingfields"):
                return Response(
                    {"error": "Permission denied: history tracking settings"},
                    status=403,
                )
            history, created = HistoryTrackingFields.objects.get_or_create(
                pk=1,
                defaults={"tracking_fields": {"tracking_fields": []}, "work_info_track": True},
            )
            if "tracking_fields" in data:
                fields = data["tracking_fields"]
                if not isinstance(fields, list):
                    fields = list(fields) if fields else []
                history.tracking_fields = {"tracking_fields": fields}
            if "work_info_track" in data:
                history.work_info_track = bool(data["work_info_track"])
            history.save()
            updated["history_tracking"] = {
                "tracking_fields": (history.tracking_fields or {}).get("tracking_fields") or [],
                "work_info_track": history.work_info_track,
            }

        if not updated:
            return Response({"error": "No valid fields to update"}, status=400)
        return Response(updated, status=200)


class PaginationSettingsAPIView(APIView):
    """GET/PATCH: Default Records Per Page (DynamicPagination)."""

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.view_dynamicpagination"))
    def get(self, request):
        from base.models import DynamicPagination

        pagination = DynamicPagination.objects.filter(user_id=request.user).first()
        return Response({"pagination": pagination.pagination if pagination else 50}, status=200)

    @method_decorator(permission_required("base.change_dynamicpagination"))
    def patch(self, request):
        from base.models import DynamicPagination
        from base.forms import DynamicPaginationForm

        pagination_value = request.data.get("pagination")
        if pagination_value is None:
            return Response({"error": "pagination is required"}, status=400)
        pagination_value = int(pagination_value)
        if pagination_value < 1:
            return Response({"error": "pagination must be at least 1"}, status=400)

        pagination, created = DynamicPagination.objects.get_or_create(
            user_id=request.user, defaults={"pagination": pagination_value}
        )
        if not created:
            pagination.pagination = pagination_value
            pagination.save()
        return Response({"pagination": pagination.pagination}, status=200)


class AccountRestrictionsAPIView(APIView):
    """GET/PATCH: Employee Account Restrictions (Restrict Login Account, Restrict Profile Edit)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm("horilla_audit.view_accountblockunblock"):
            return Response({"error": "Permission denied"}, status=403)
        from horilla_audit.models import AccountBlockUnblock
        from employee.models import ProfileEditFeature

        enabled_block_unblock = (
            AccountBlockUnblock.objects.exists()
            and AccountBlockUnblock.objects.first().is_enabled
        )
        enabled_profile_edit = (
            ProfileEditFeature.objects.exists()
            and ProfileEditFeature.objects.first().is_enabled
        )
        return Response(
            {
                "restrict_login_account": enabled_block_unblock,
                "restrict_profile_edit": enabled_profile_edit,
            },
            status=200,
        )

    def patch(self, request):
        from horilla_audit.models import AccountBlockUnblock
        from employee.models import ProfileEditFeature
        from accessibility.models import DefaultAccessibility
        from accessibility.accessibility import ACCESSBILITY_FEATURE

        data = request.data
        updated = {}

        if "restrict_login_account" in data:
            if not request.user.has_perm("horilla_audit.change_accountblockunblock"):
                return Response({"error": "Permission denied: change account block/unblock"}, status=403)
            block_unblock, created = AccountBlockUnblock.objects.get_or_create(
                pk=1, defaults={"is_enabled": False}
            )
            block_unblock.is_enabled = bool(data["restrict_login_account"])
            block_unblock.save()
            updated["restrict_login_account"] = block_unblock.is_enabled

        if "restrict_profile_edit" in data:
            if not request.user.has_perm("employee.change_employee"):
                return Response({"error": "Permission denied: change employee"}, status=403)
            enabled = bool(data["restrict_profile_edit"])
            profile_edit, created = ProfileEditFeature.objects.get_or_create(
                pk=1, defaults={"is_enabled": False}
            )
            profile_edit.is_enabled = enabled
            profile_edit.save()
            
            # Handle DefaultAccessibility for profile_edit feature (matching Django view)
            feature = DefaultAccessibility.objects.filter(feature="profile_edit").first()
            if enabled and not feature:
                DefaultAccessibility.objects.create(
                    feature="profile_edit", filter={"feature": ["profile_edit"]}
                )
            elif not enabled and feature:
                feature.delete()
            
            updated["restrict_profile_edit"] = profile_edit.is_enabled

        if not updated:
            return Response({"error": "No valid fields to update"}, status=400)
        return Response(updated, status=200)


class BadgePrefixAPIView(APIView):
    """GET/PATCH: Badge Prefix (EmployeeGeneralSetting)."""

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("employee.view_employeegeneralsetting"))
    def get(self, request):
        from employee.models import EmployeeGeneralSetting

        prefix_instance = EmployeeGeneralSetting.objects.first()
        return Response(
            {
                "badge_prefix": prefix_instance.badge_id_prefix if prefix_instance else "",
                "company_id": prefix_instance.company_id.id if prefix_instance and prefix_instance.company_id else None,
            },
            status=200,
        )

    @method_decorator(permission_required("employee.change_employeegeneralsetting"))
    def patch(self, request):
        from employee.models import EmployeeGeneralSetting
        from base.models import Company

        badge_prefix = request.data.get("badge_prefix", "")
        company_id = request.data.get("company_id")

        prefix_instance = EmployeeGeneralSetting.objects.first()
        if not prefix_instance:
            prefix_instance = EmployeeGeneralSetting.objects.create()

        prefix_instance.badge_id_prefix = badge_prefix
        if company_id:
            try:
                prefix_instance.company_id = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                return Response({"error": "Company not found"}, status=400)
        else:
            prefix_instance.company_id = None
        prefix_instance.save()

        return Response(
            {
                "badge_prefix": prefix_instance.badge_id_prefix,
                "company_id": prefix_instance.company_id.id if prefix_instance.company_id else None,
            },
            status=200,
        )


class EncashmentSettingsAPIView(APIView):
    """GET/PATCH: Encashment Redeem Condition (bonus_unit, leave_unit)."""

    permission_classes = [IsAuthenticated]

    def _check_payroll(self):
        from django.apps import apps

        if not apps.is_installed("payroll"):
            return None, None
        from horilla.methods import get_horilla_model_class

        EncashmentGeneralSettings = get_horilla_model_class(
            app_label="payroll", model="encashmentgeneralsettings"
        )
        return EncashmentGeneralSettings, None

    def get(self, request):
        EncashmentGeneralSettings, _ = self._check_payroll()
        if not EncashmentGeneralSettings:
            return Response({"error": "Payroll app not installed"}, status=404)
        if not request.user.has_perm("payroll.view_encashmentgeneralsetting"):
            return Response({"error": "Permission denied"}, status=403)

        encashment = EncashmentGeneralSettings.objects.first()
        return Response(
            {
                "bonus_unit": encashment.bonus_amount if encashment else None,
                "leave_unit": encashment.leave_amount if encashment else None,
            },
            status=200,
        )

    def patch(self, request):
        EncashmentGeneralSettings, _ = self._check_payroll()
        if not EncashmentGeneralSettings:
            return Response({"error": "Payroll app not installed"}, status=404)
        if not request.user.has_perm("payroll.change_encashmentgeneralsetting"):
            return Response({"error": "Permission denied"}, status=403)

        bonus_unit = request.data.get("bonus_unit")
        leave_unit = request.data.get("leave_unit")

        encashment = EncashmentGeneralSettings.objects.first()
        if not encashment:
            encashment = EncashmentGeneralSettings.objects.create()

        if bonus_unit is not None:
            encashment.bonus_amount = bonus_unit
        if leave_unit is not None:
            encashment.leave_amount = leave_unit
        encashment.save()

        return Response(
            {"bonus_unit": encashment.bonus_amount, "leave_unit": encashment.leave_amount},
            status=200,
        )


class CurrencySettingsAPIView(APIView):
    """GET/PATCH: Currency (currency_symbol, position, company_id)."""

    permission_classes = [IsAuthenticated]

    def _check_payroll(self):
        from django.apps import apps

        if not apps.is_installed("payroll"):
            return None
        from horilla.methods import get_horilla_model_class

        PayrollSettings = get_horilla_model_class(
            app_label="payroll", model="payrollsettings"
        )
        return PayrollSettings

    def get(self, request):
        PayrollSettings = self._check_payroll()
        if not PayrollSettings:
            return Response({"error": "Payroll app not installed"}, status=404)
        if not request.user.has_perm("payroll.view_payrollsettings"):
            return Response({"error": "Permission denied"}, status=403)

        currency = PayrollSettings.objects.first()
        return Response(
            {
                "currency_symbol": currency.currency_symbol if currency else None,
                "position": currency.position if currency else None,
                "company_id": currency.company_id.id if currency and currency.company_id else None,
            },
            status=200,
        )

    def patch(self, request):
        PayrollSettings = self._check_payroll()
        if not PayrollSettings:
            return Response({"error": "Payroll app not installed"}, status=404)
        if not request.user.has_perm("payroll.change_payrollsettings"):
            return Response({"error": "Permission denied"}, status=403)

        from base.models import Company

        currency_symbol = request.data.get("currency_symbol")
        position = request.data.get("position")
        company_id = request.data.get("company_id")

        currency = PayrollSettings.objects.first()
        if not currency:
            currency = PayrollSettings.objects.create()

        if currency_symbol is not None:
            currency.currency_symbol = currency_symbol
        if position is not None:
            currency.position = position
        if company_id is not None:
            if company_id:
                try:
                    currency.company_id = Company.objects.get(id=company_id)
                except Company.DoesNotExist:
                    return Response({"error": "Company not found"}, status=400)
            else:
                currency.company_id = None
        currency.save()

        return Response(
            {
                "currency_symbol": currency.currency_symbol,
                "position": currency.position,
                "company_id": currency.company_id.id if currency.company_id else None,
            },
            status=200,
        )


class ResignationRequestAPIView(APIView):
    """GET/PATCH: Resignation Request toggle."""

    permission_classes = [IsAuthenticated]

    def _check_offboarding(self):
        from django.apps import apps

        if not apps.is_installed("offboarding"):
            return None
        from horilla.methods import get_horilla_model_class

        OffboardingGeneralSetting = get_horilla_model_class(
            app_label="offboarding", model="offboardinggeneralsetting"
        )
        return OffboardingGeneralSetting

    def get(self, request):
        OffboardingGeneralSetting = self._check_offboarding()
        if not OffboardingGeneralSetting:
            return Response({"error": "Offboarding app not installed"}, status=404)
        if not request.user.has_perm("offboarding.view_offboardinggeneralsetting"):
            return Response({"error": "Permission denied"}, status=403)

        offboarding = OffboardingGeneralSetting.objects.first()
        return Response(
            {"resignation_request": offboarding.resignation_request if offboarding else False},
            status=200,
        )

    def patch(self, request):
        OffboardingGeneralSetting = self._check_offboarding()
        if not OffboardingGeneralSetting:
            return Response({"error": "Offboarding app not installed"}, status=404)
        if not request.user.has_perm("offboarding.change_offboardinggeneralsetting"):
            return Response({"error": "Permission denied"}, status=403)

        resignation_request = request.data.get("resignation_request")
        if resignation_request is None:
            return Response({"error": "resignation_request is required"}, status=400)

        offboarding = OffboardingGeneralSetting.objects.first()
        if not offboarding:
            offboarding = OffboardingGeneralSetting.objects.create()

        offboarding.resignation_request = bool(resignation_request)
        offboarding.save()

        return Response({"resignation_request": offboarding.resignation_request}, status=200)


class TimeRunnerAPIView(APIView):
    """GET/PATCH: Time Runner (At-Work Tracker) toggle."""

    permission_classes = [IsAuthenticated]

    def _check_attendance(self):
        from django.apps import apps

        if not apps.is_installed("attendance"):
            return None
        from horilla.methods import get_horilla_model_class

        AttendanceGeneralSetting = get_horilla_model_class(
            app_label="attendance", model="attendancegeneralsetting"
        )
        return AttendanceGeneralSetting

    def get(self, request):
        AttendanceGeneralSetting = self._check_attendance()
        if not AttendanceGeneralSetting:
            return Response({"error": "Attendance app not installed"}, status=404)
        if not request.user.has_perm("attendance.view_attendancegeneralsetting"):
            return Response({"error": "Permission denied"}, status=403)

        attendance = AttendanceGeneralSetting.objects.first()
        return Response(
            {"time_runner": attendance.time_runner if attendance else False},
            status=200,
        )

    def patch(self, request):
        AttendanceGeneralSetting = self._check_attendance()
        if not AttendanceGeneralSetting:
            return Response({"error": "Attendance app not installed"}, status=404)
        if not request.user.has_perm("attendance.change_attendancegeneralsetting"):
            return Response({"error": "Permission denied"}, status=403)

        time_runner = request.data.get("time_runner")
        if time_runner is None:
            return Response({"error": "time_runner is required"}, status=400)

        attendance = AttendanceGeneralSetting.objects.first()
        if not attendance:
            attendance = AttendanceGeneralSetting.objects.create()

        attendance.time_runner = bool(time_runner)
        attendance.save()

        return Response({"time_runner": attendance.time_runner}, status=200)


class NoticePeriodAPIView(APIView):
    """GET/PATCH: Notice Period (default notice_period - stored in PayrollGeneralSetting)."""

    permission_classes = [IsAuthenticated]

    def _check_payroll(self):
        from django.apps import apps

        if not apps.is_installed("payroll"):
            return None
        from horilla.methods import get_horilla_model_class

        PayrollGeneralSetting = get_horilla_model_class(
            app_label="payroll", model="payrollgeneralsetting"
        )
        return PayrollGeneralSetting

    def get(self, request):
        PayrollGeneralSetting = self._check_payroll()
        if not PayrollGeneralSetting:
            return Response({"error": "Payroll app not installed"}, status=404)
        if not request.user.has_perm("payroll.view_payrollgeneralsetting"):
            return Response({"error": "Permission denied"}, status=403)

        payroll_gen = PayrollGeneralSetting.objects.first()
        notice_period_days = (
            getattr(payroll_gen, "notice_period", None) if payroll_gen else None
        )
        return Response({"notice_period_days": notice_period_days}, status=200)

    def patch(self, request):
        PayrollGeneralSetting = self._check_payroll()
        if not PayrollGeneralSetting:
            return Response({"error": "Payroll app not installed"}, status=404)
        if not request.user.has_perm("payroll.change_payrollgeneralsetting"):
            return Response({"error": "Permission denied"}, status=403)

        notice_period_days = request.data.get("notice_period_days")
        if notice_period_days is None:
            return Response({"error": "notice_period_days is required"}, status=400)

        payroll_gen = PayrollGeneralSetting.objects.first()
        if not payroll_gen:
            payroll_gen = PayrollGeneralSetting.objects.create()

        payroll_gen.notice_period = int(notice_period_days)
        payroll_gen.save()

        return Response({"notice_period_days": payroll_gen.notice_period}, status=200)


def _get_company_for_date_time(request):
    """
    Resolve the Company instance to use for date/time format (read or write).
    Mirrors base.views get_date_format logic: superuser can target a company;
    otherwise use the authenticated user's employee work info company.
    """
    from base.models import Company
    from employee.models import EmployeeWorkInformation

    user = request.user
    if user.is_superuser:
        company_id = request.query_params.get("company_id") or getattr(
            request, "data", {}
        ).get("company_id")
        if company_id:
            try:
                return Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                pass
        return Company.objects.first()
    employee = getattr(user, "employee_get", None)
    if not employee:
        return None
    info = EmployeeWorkInformation.objects.filter(employee_id=employee).first()
    return info.company_id if info else None


class DateTimeSettingsAPIView(APIView):
    """
    GET: Return current date_format and time_format for the user's company.
    PATCH: Update date_format and/or time_format (requires base.change_company).
    """

    permission_classes = [IsAuthenticated]
    DATE_DEFAULT = "MMM. D, YYYY"
    TIME_DEFAULT = "hh:mm A"

    def get(self, request):
        company = _get_company_for_date_time(request)
        date_format = company.date_format if company else self.DATE_DEFAULT
        time_format = company.time_format if company else self.TIME_DEFAULT
        if not date_format:
            date_format = self.DATE_DEFAULT
        if not time_format:
            time_format = self.TIME_DEFAULT
        return Response(
            {"date_format": date_format, "time_format": time_format},
            status=200,
        )

    @method_decorator(permission_required("base.change_company"))
    def patch(self, request):
        company = _get_company_for_date_time(request)
        if not company:
            return Response(
                {"error": "No company found. Update the company field for the user."},
                status=400,
            )
        data = request.data
        updated = {}
        if "date_format" in data and data["date_format"]:
            company.date_format = data["date_format"]
            company.save()
            updated["date_format"] = company.date_format
        if "time_format" in data and data["time_format"]:
            company.time_format = data["time_format"]
            company.save()
            updated["time_format"] = company.time_format
        if not updated:
            return Response(
                {"error": "Provide date_format and/or time_format to update."},
                status=400,
            )
        return Response(updated, status=200)


class AuditTagListCreateView(APIView):
    """List all history (audit) tags and create new ones. Requires horilla_audit.view_audittag / add_audittag."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from horilla_audit.models import AuditTag

        if not request.user.has_perm("horilla_audit.view_audittag"):
            return Response({"error": "Permission denied"}, status=403)
        tags = AuditTag.objects.all().order_by("id")
        data = [{"id": t.id, "title": t.title, "highlight": t.highlight} for t in tags]
        return Response(data, status=200)

    @method_decorator(permission_required("horilla_audit.add_audittag"))
    def post(self, request):
        from horilla_audit.models import AuditTag

        title = (request.data.get("title") or "").strip()
        if not title:
            return Response({"error": "Title is required"}, status=400)
        if len(title) > 20:
            return Response({"error": "Title must be at most 20 characters"}, status=400)
        tag = AuditTag.objects.create(
            title=title,
            highlight=bool(request.data.get("highlight")),
        )
        return Response(
            {"id": tag.id, "title": tag.title, "highlight": tag.highlight},
            status=201,
        )


class AuditTagDetailView(APIView):
    """Retrieve, update, or delete a single history (audit) tag."""

    permission_classes = [IsAuthenticated]

    def _get_tag(self, pk):
        from horilla_audit.models import AuditTag

        try:
            return AuditTag.objects.get(pk=pk)
        except AuditTag.DoesNotExist:
            return None

    def get(self, request, pk):
        if not request.user.has_perm("horilla_audit.view_audittag"):
            return Response({"error": "Permission denied"}, status=403)
        tag = self._get_tag(pk)
        if not tag:
            return Response({"error": "History tag not found"}, status=404)
        return Response(
            {"id": tag.id, "title": tag.title, "highlight": tag.highlight},
            status=200,
        )

    @method_decorator(permission_required("horilla_audit.change_audittag"))
    def put(self, request, pk):
        from horilla_audit.models import AuditTag

        tag = self._get_tag(pk)
        if not tag:
            return Response({"error": "History tag not found"}, status=404)
        title = (request.data.get("title") or "").strip()
        if not title:
            return Response({"error": "Title is required"}, status=400)
        if len(title) > 20:
            return Response({"error": "Title must be at most 20 characters"}, status=400)
        tag.title = title
        tag.highlight = bool(request.data.get("highlight"))
        tag.save()
        return Response(
            {"id": tag.id, "title": tag.title, "highlight": tag.highlight},
            status=200,
        )

    @method_decorator(permission_required("horilla_audit.delete_audittag"))
    def delete(self, request, pk):
        tag = self._get_tag(pk)
        if not tag:
            return Response({"error": "History tag not found"}, status=404)
        tag.delete()
        return Response(status=204)


def _get_models_in_app(app_name):
    """Get models for an app (mirrors base.views get_models_in_app)."""
    from django.apps import apps

    try:
        return apps.get_app_config(app_name).get_models()
    except LookupError:
        return []


class EmployeePermissionsMetaAPIView(APIView):
    """
    GET: Return permission structure for UI (apps -> models -> permissions)
    and optionally list of employees with permissions (search, pagination).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from django.apps import apps
        from employee.filters import EmployeeFilter
        from employee.models import Employee
        from horilla.horilla_settings import NO_PERMISSION_MODALS

        if not request.user.has_perm("auth.view_permission"):
            return Response({"error": "Permission denied"}, status=403)

        # Get all installed apps (not just APPS) - filter out Django system apps
        installed_apps = [
            app_config.name
            for app_config in apps.get_app_configs()
            if not app_config.name.startswith("django.")
            and app_config.name not in ["contenttypes", "sessions", "messages", "staticfiles", "admin"]
            and app_config.name not in ["notifications", "mathfilters", "corsheaders", "simple_history", "django_filters", "rest_framework", "widget_tweaks", "django_apscheduler", "chart_bot"]
        ]
        
        # Order apps: base apps first, then others alphabetically
        priority_apps = ["base", "employee", "horilla_documents", "horilla_automations", "recruitment", "leave", "pms", "onboarding", "asset", "attendance", "payroll", "biometric", "helpdesk", "offboarding", "project"]
        ordered_apps = []
        for app in priority_apps:
            if app in installed_apps:
                ordered_apps.append(app)
        for app in sorted(installed_apps):
            if app not in ordered_apps:
                ordered_apps.append(app)

        # Build permission structure: app -> models -> permissions
        structure = []
        for app_name in ordered_apps:
            app_models = []
            for model in _get_models_in_app(app_name):
                if getattr(model, "_meta", None) and getattr(
                    model._meta, "model_name", None
                ) not in NO_PERMISSION_MODALS:
                    try:
                        ct = ContentType.objects.get_for_model(model)
                        perms = Permission.objects.filter(content_type=ct).order_by(
                            "codename"
                        )
                        perms_list = [
                            {"id": p.id, "codename": p.codename, "name": p.name or p.codename}
                            for p in perms
                        ]
                        if perms_list:
                            app_models.append(
                                {
                                    "model_name": model._meta.model_name,
                                    "verbose_name": str(
                                        getattr(model._meta, "verbose_name", None) or model._meta.model_name
                                    ).capitalize(),
                                    "permissions": perms_list,
                                }
                            )
                    except Exception:
                        continue
            if app_models:
                structure.append(
                    {
                        "app": app_name.capitalize().replace("_", " "),
                        "app_models": app_models,
                    }
                )

        # Optional: list employees with permissions (search from query params)
        employees_qs = Employee.objects.filter(
            employee_user_id__user_permissions__isnull=False
        ).distinct()
        filter_qs = EmployeeFilter(data=request.query_params, queryset=employees_qs).qs
        page = int(request.query_params.get("page", 1))
        page_size = min(int(request.query_params.get("page_size", 20)), 100)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = filter_qs[start:end]
        employees_list = []
        for emp in paginated:
            user = getattr(emp, "employee_user_id", None)
            perm_ids = (
                list(user.user_permissions.values_list("id", flat=True))
                if user
                else []
            )
            job_info = getattr(emp, "employee_work_info", None)
            employees_list.append(
                {
                    "id": emp.id,
                    "employee_first_name": getattr(emp, "employee_first_name", "") or "",
                    "employee_last_name": getattr(emp, "employee_last_name", "") or "",
                    "job_position": (
                        getattr(job_info.job_position_id, "job_position", None)
                        if job_info and getattr(job_info, "job_position_id", None)
                        else None
                    ),
                    "department": (
                        getattr(job_info.department_id, "department", None)
                        if job_info and getattr(job_info, "department_id", None)
                        else None
                    ),
                    "job_role": (
                        getattr(job_info.job_role_id, "job_role", None)
                        if job_info and getattr(job_info, "job_role_id", None)
                        else None
                    ),
                    "permission_ids": perm_ids,
                }
            )

        return Response(
            {
                "permission_structure": structure,
                "employees": employees_list,
                "count": filter_qs.count(),
                "no_permission_models": NO_PERMISSION_MODALS,  # Return excluded models list for frontend filtering
            },
            status=200,
        )


class EmployeePermissionsGetAPIView(APIView):
    """GET: Get an employee's current assigned permissions."""

    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id=None):
        from employee.models import Employee

        emp_id = employee_id or request.query_params.get("employee_id")
        if not emp_id:
            return Response({"error": "employee_id is required"}, status=400)
        
        emp = Employee.objects.filter(id=emp_id).first()
        if not emp or not getattr(emp, "employee_user_id", None):
            return Response({"error": "Employee or user not found"}, status=404)
        
        user = emp.employee_user_id
        permission_ids = list(user.user_permissions.values_list("id", flat=True))
        
        return Response(
            {"employee_id": emp_id, "permission_ids": permission_ids},
            status=200,
        )


class EmployeePermissionsAssignAPIView(APIView):
    """POST: Assign permissions to one or more employees (replace user_permissions)."""

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("auth.add_permission"))
    def post(self, request):
        from django.contrib.auth.models import Permission
        from employee.models import Employee

        # Support both single employee_id (backward compatibility) and employee_ids (multiple)
        employee_id = request.data.get("employee_id")
        employee_ids = request.data.get("employee_ids", [])
        permission_ids = request.data.get("permission_ids", [])
        
        # If single employee_id is provided, convert to list
        if employee_id is not None:
            employee_ids = [employee_id] if not employee_ids else employee_ids
        
        if not employee_ids:
            return Response({"error": "employee_id or employee_ids is required"}, status=400)
        
        if not isinstance(employee_ids, list):
            employee_ids = [employee_ids]
        
        if permission_ids is None:
            permission_ids = []
        if not isinstance(permission_ids, list):
            permission_ids = list(permission_ids) if permission_ids else []
        
        # Get all employees
        employees = Employee.objects.filter(id__in=employee_ids)
        if not employees.exists():
            return Response({"error": "No employees found"}, status=404)
        
        # Get users for these employees
        users = []
        for emp in employees:
            if getattr(emp, "employee_user_id", None):
                users.append(emp.employee_user_id)
        
        if not users:
            return Response({"error": "No users found for the selected employees"}, status=404)
        
        # Get permissions
        perms = Permission.objects.filter(id__in=permission_ids)
        
        # Assign permissions to all users
        for user in users:
            user.user_permissions.set(perms)
        
        return Response(
            {
                "message": f"Permissions updated for {len(users)} employee(s)",
                "employee_count": len(users),
                "permission_ids": list(perms.values_list("id", flat=True)),
            },
            status=200,
        )


def _get_accessibility_filter_options():
    """Build options for each filter field (id + label) for frontend dropdowns."""
    from django.contrib.auth.models import Group, Permission
    from base.models import Company, Department, JobPosition, JobRole, WorkType
    from employee.models import EmployeeType
    from base.models import EmployeeShift
    from employee.models import EmployeeTag

    options = {}
    # employee_work_info__department_id
    options["employee_work_info__department_id"] = [
        {"id": d.id, "name": getattr(d, "department", str(d))}
        for d in Department.objects.all()[:500]
    ]
    # employee_work_info__job_position_id
    options["employee_work_info__job_position_id"] = [
        {"id": j.id, "name": getattr(j, "job_position", str(j))}
        for j in JobPosition.objects.all()[:500]
    ]
    # employee_work_info__company_id
    options["employee_work_info__company_id"] = [
        {"id": c.id, "name": getattr(c, "company", str(c))}
        for c in Company.objects.all()[:100]
    ]
    # employee_work_info__job_role_id
    options["employee_work_info__job_role_id"] = [
        {"id": j.id, "name": getattr(j, "job_role", str(j))}
        for j in JobRole.objects.all()[:500]
    ]
    # employee_work_info__work_type_id
    options["employee_work_info__work_type_id"] = [
        {"id": w.id, "name": getattr(w, "work_type", str(w))}
        for w in WorkType.objects.all()[:100]
    ]
    # employee_work_info__employee_type_id
    options["employee_work_info__employee_type_id"] = [
        {"id": e.id, "name": getattr(e, "employee_type", str(e))}
        for e in EmployeeType.objects.all()[:100]
    ]
    # employee_work_info__shift_id
    options["employee_work_info__shift_id"] = [
        {"id": s.id, "name": getattr(s, "employee_shift", str(s))}
        for s in EmployeeShift.objects.all()[:100]
    ]
    # employee_work_info__tags (EmployeeTag)
    options["employee_work_info__tags"] = [
        {"id": t.id, "name": getattr(t, "title", str(t))}
        for t in EmployeeTag.objects.all()[:200]
    ]
    # employee_user_id__groups
    options["employee_user_id__groups"] = [
        {"id": g.id, "name": g.name}
        for g in Group.objects.all()[:100]
    ]
    # employee_user_id__user_permissions - too many; return empty, frontend can search or skip
    options["employee_user_id__user_permissions"] = []
    # pk, exluded_employees - employee multiselect; frontend uses employee search
    options["pk"] = []
    options["exluded_employees"] = []
    return options


class AccessibilitySettingsAPIView(APIView):
    """
    GET: Return accessibility features, saved settings per feature, and filter field options.
    POST: Save accessibility for a feature (exclude_all, filter dict).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from accessibility.accessibility import ACCESSBILITY_FEATURE
        from accessibility.models import DefaultAccessibility

        if not request.user.has_perm("auth.change_permission"):
            return Response({"error": "Permission denied"}, status=403)
        features = [
            {"feature": f[0], "display": str(f[1])}
            for f in ACCESSBILITY_FEATURE
        ]
        settings_map = {}
        for acc in DefaultAccessibility.objects.all():
            filt = acc.filter or {}
            # Normalize to list values for frontend
            filter_normalized = {}
            for k, v in filt.items():
                if k in ("feature", "csrfmiddlewaretoken"):
                    continue
                if isinstance(v, list):
                    filter_normalized[k] = [int(x) for x in v if str(x).isdigit()]
                elif v and str(v).isdigit():
                    filter_normalized[k] = [int(v)]
                elif isinstance(v, (list, tuple)):
                    filter_normalized[k] = [int(x) for x in v if str(x).isdigit()]
            settings_map[acc.feature] = {
                "exclude_all": acc.exclude_all,
                "filter": filter_normalized,
            }
        for f in features:
            if f["feature"] not in settings_map:
                settings_map[f["feature"]] = {"exclude_all": False, "filter": {}}
        return Response(
            {
                "features": features,
                "settings": settings_map,
                "filter_field_options": _get_accessibility_filter_options(),
                "filter_field_labels": {
                    "pk": "Employee",
                    "exluded_employees": "Exclude Employees",
                    "employee_work_info__job_position_id": "Job Position",
                    "employee_work_info__department_id": "Department",
                    "employee_work_info__work_type_id": "Work Type",
                    "employee_work_info__employee_type_id": "Employee Type",
                    "employee_work_info__job_role_id": "Job Role",
                    "employee_work_info__company_id": "Company",
                    "employee_work_info__shift_id": "Shift",
                    "employee_work_info__tags": "Tags",
                    "employee_user_id__groups": "Groups",
                    "employee_user_id__user_permissions": "Permissions",
                },
            },
            status=200,
        )

    @method_decorator(permission_required("auth.change_permission"))
    def post(self, request):
        from accessibility.filters import AccessibilityFilter
        from accessibility.models import DefaultAccessibility

        feature = request.data.get("feature")
        if not feature:
            return Response({"error": "feature is required"}, status=400)
        exclude_all = bool(request.data.get("exclude_all"))
        filter_data = request.data.get("filter") or {}
        if not isinstance(filter_data, dict):
            return Response({"error": "filter must be an object"}, status=400)
        # Build data dict for AccessibilityFilter (values as lists)
        data_dict = {"feature": feature, "exclude_all": "on" if exclude_all else ""}
        for k, v in filter_data.items():
            if isinstance(v, list):
                data_dict[k] = v
            else:
                data_dict[k] = [v] if v is not None else []
        acc, _ = DefaultAccessibility.objects.get_or_create(
            feature=feature,
            defaults={"filter": {}, "exclude_all": False},
        )
        acc.exclude_all = exclude_all
        acc.filter = data_dict
        acc.save()
        employees = AccessibilityFilter(data=data_dict).qs
        acc.employees.set(employees)
        return Response(
            {"message": "Accessibility filter saved", "feature": feature},
            status=200,
        )


class UserGroupListCreateView(APIView):
    """List user groups (with search, pagination) or create a new group."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.contrib.auth.models import Group

        if not request.user.has_perm("auth.view_group"):
            return Response({"error": "Permission denied"}, status=403)
        search = (request.query_params.get("search") or "").strip()
        qs = Group.objects.all().order_by("name")
        if search:
            qs = qs.filter(name__icontains=search)
        page = int(request.query_params.get("page", 1))
        page_size = min(int(request.query_params.get("page_size", 20)), 100)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = qs[start:end]
        count = qs.count()
        from employee.models import Employee

        data = []
        for g in paginated:
            perm_ids = list(g.permissions.values_list("id", flat=True))
            user_count = g.user_set.count()
            member_employee_ids = list(
                Employee.objects.filter(employee_user_id__groups=g).values_list("id", flat=True)
            )
            data.append(
                {
                    "id": g.id,
                    "name": g.name,
                    "permission_ids": perm_ids,
                    "user_count": user_count,
                    "member_employee_ids": member_employee_ids,
                }
            )
        return Response({"results": data, "count": count}, status=200)

    @method_decorator(permission_required("auth.add_group"))
    def post(self, request):
        from django.contrib.auth.models import Group, Permission

        name = (request.data.get("name") or "").strip()
        if not name or len(name) < 4:
            return Response(
                {"error": "Group name is required and must be at least 4 characters"},
                status=400,
            )
        if Group.objects.filter(name=name).exists():
            return Response({"error": "A group with this name already exists"}, status=400)
        permission_ids = request.data.get("permission_ids") or []
        if not isinstance(permission_ids, list):
            permission_ids = list(permission_ids) if permission_ids else []
        group = Group.objects.create(name=name)
        perms = Permission.objects.filter(id__in=permission_ids)
        group.permissions.set(perms)
        return Response(
            {
                "id": group.id,
                "name": group.name,
                "permission_ids": list(group.permissions.values_list("id", flat=True)),
                "user_count": 0,
            },
            status=201,
        )


class UserGroupDetailView(APIView):
    """Retrieve, update, or delete a user group."""

    permission_classes = [IsAuthenticated]

    def _get_group(self, pk):
        from django.contrib.auth.models import Group

        try:
            return Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return None

    def get(self, request, pk):
        if not request.user.has_perm("auth.view_group"):
            return Response({"error": "Permission denied"}, status=403)
        group = self._get_group(pk)
        if not group:
            return Response({"error": "Group not found"}, status=404)
        perm_ids = list(group.permissions.values_list("id", flat=True))
        user_count = group.user_set.count()
        from employee.models import Employee

        member_employee_ids = list(
            Employee.objects.filter(employee_user_id__groups=group).values_list("id", flat=True)
        )
        return Response(
            {
                "id": group.id,
                "name": group.name,
                "permission_ids": perm_ids,
                "user_count": user_count,
                "member_employee_ids": member_employee_ids,
            },
            status=200,
        )

    @method_decorator(permission_required("auth.change_group"))
    def put(self, request, pk):
        from django.contrib.auth.models import Group, Permission

        group = self._get_group(pk)
        if not group:
            return Response({"error": "Group not found"}, status=404)
        data = request.data
        if "name" in data:
            name = (data.get("name") or "").strip()
            if len(name) < 4:
                return Response(
                    {"error": "Group name must be at least 4 characters"},
                    status=400,
                )
            if Group.objects.filter(name=name).exclude(pk=pk).exists():
                return Response({"error": "A group with this name already exists"}, status=400)
            group.name = name
            group.save()
        if "permission_ids" in data:
            perm_ids = data["permission_ids"]
            if not isinstance(perm_ids, list):
                perm_ids = list(perm_ids) if perm_ids else []
            perms = Permission.objects.filter(id__in=perm_ids)
            group.permissions.set(perms)
        perm_ids = list(group.permissions.values_list("id", flat=True))
        user_count = group.user_set.count()
        return Response(
            {
                "id": group.id,
                "name": group.name,
                "permission_ids": perm_ids,
                "user_count": user_count,
            },
            status=200,
        )

    @method_decorator(permission_required("auth.delete_group"))
    def delete(self, request, pk):
        group = self._get_group(pk)
        if not group:
            return Response({"error": "Group not found"}, status=404)
        group.delete()
        return Response(status=204)


class UserGroupAssignView(APIView):
    """Assign employees to a group (replace group membership for those users)."""

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("auth.change_group"))
    def post(self, request):
        from django.contrib.auth.models import Group
        from employee.models import Employee

        group_id = request.data.get("group_id")
        employee_ids = request.data.get("employee_ids") or []
        if group_id is None:
            return Response({"error": "group_id is required"}, status=400)
        if not isinstance(employee_ids, list):
            employee_ids = list(employee_ids) if employee_ids else []
        group = Group.objects.filter(id=group_id).first()
        if not group:
            return Response({"error": "Group not found"}, status=404)
        employees = Employee.objects.filter(id__in=employee_ids)
        users = [e.employee_user_id for e in employees if getattr(e, "employee_user_id", None)]
        group.user_set.set(users)
        return Response(
            {"message": "Group assigned", "user_count": group.user_set.count()},
            status=200,
        )


def _mail_server_payload(config, include_password=False):
    """Build response payload for DynamicEmailConfiguration (exclude password by default)."""
    from base.models import DynamicEmailConfiguration

    data = {
        "id": config.id,
        "host": config.host,
        "port": config.port,
        "from_email": config.from_email,
        "username": config.username,
        "display_name": config.display_name,
        "use_tls": config.use_tls,
        "use_ssl": config.use_ssl,
        "fail_silently": config.fail_silently,
        "is_primary": config.is_primary,
        "use_dynamic_display_name": config.use_dynamic_display_name,
        "timeout": config.timeout,
        "company_id": config.company_id.id if config.company_id else None,
    }
    if include_password and config.password:
        data["password"] = config.password
    if config.company_id:
        data["company_name"] = getattr(config.company_id, "company", None)
    return data


class MailServerListCreateView(APIView):
    """List all mail servers or create one (matches Django mail_server_conf / mail_server_create_or_update)."""

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.view_dynamicemailconfiguration"))
    def get(self, request):
        from base.models import DynamicEmailConfiguration

        configs = DynamicEmailConfiguration.objects.all().order_by("-is_primary", "id")
        primary_exists = DynamicEmailConfiguration.objects.filter(is_primary=True).exists()
        data = [_mail_server_payload(c) for c in configs]
        return Response(
            {"results": data, "primary_mail_exists": primary_exists},
            status=200,
        )

    @method_decorator(permission_required("base.add_dynamicemailconfiguration"))
    def post(self, request):
        from base.forms import DynamicMailConfForm
        from base.models import DynamicEmailConfiguration

        form = DynamicMailConfForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=400)
        obj = form.save()
        return Response(_mail_server_payload(obj), status=201)


class MailServerDetailView(APIView):
    """Retrieve, update, or delete a mail server."""

    permission_classes = [IsAuthenticated]

    def _get_config(self, pk):
        from base.models import DynamicEmailConfiguration

        try:
            return DynamicEmailConfiguration.objects.get(pk=pk)
        except DynamicEmailConfiguration.DoesNotExist:
            return None

    @method_decorator(permission_required("base.view_dynamicemailconfiguration"))
    def get(self, request, pk):
        config = self._get_config(pk)
        if not config:
            return Response({"error": "Mail server not found"}, status=404)
        return Response(_mail_server_payload(config), status=200)

    @method_decorator(permission_required("base.change_dynamicemailconfiguration"))
    def put(self, request, pk):
        from base.forms import DynamicMailConfForm
        from base.models import DynamicEmailConfiguration

        config = self._get_config(pk)
        if not config:
            return Response({"error": "Mail server not found"}, status=404)
        data = dict(request.data)
        if data.get("password") in (None, ""):
            data.pop("password", None)
        form = DynamicMailConfForm(data, instance=config)
        if not form.is_valid():
            return Response(form.errors, status=400)
        obj = form.save()
        return Response(_mail_server_payload(obj), status=200)

    @method_decorator(permission_required("base.delete_dynamicemailconfiguration"))
    def delete(self, request, pk):
        from base.models import DynamicEmailConfiguration

        config = self._get_config(pk)
        if not config:
            return Response({"error": "Mail server not found"}, status=404)
        total = DynamicEmailConfiguration.objects.count()
        if config.is_primary and total == 1:
            return Response(
                {"error": "You have only 1 Mail server configuration that can't be deleted"},
                status=400,
            )
        if config.is_primary and total > 1:
            others = list(
                DynamicEmailConfiguration.objects.exclude(id=pk).values_list("id", "username")
            )
            return Response(
                {
                    "error": "Cannot delete primary mail server without replacing it.",
                    "replace_required": True,
                    "other_servers": [{"id": o[0], "username": o[1]} for o in others],
                },
                status=400,
            )
        config.delete()
        return Response(status=204)


class MailServerTestEmailView(APIView):
    """Send a test email using the given mail server (matches Django mail_server_test_email)."""

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.view_dynamicemailconfiguration"))
    def post(self, request):
        from django.conf import settings
        from os import path

        from django.utils.html import strip_tags
        from django.utils.translation import gettext as _
        from email.mime.image import MIMEImage
        from datetime import datetime

        from base.backends import ConfiguredEmailBackend
        from base.models import DynamicEmailConfiguration
        from django.core.mail import EmailMultiAlternatives

        instance_id = request.data.get("instance_id") or request.data.get("id")
        to_email = request.data.get("to_email")
        if not instance_id or not to_email:
            return Response(
                {"error": "instance_id and to_email are required"},
                status=400,
            )
        config = DynamicEmailConfiguration.objects.filter(id=instance_id).first()
        if not config:
            return Response({"error": "Mail server not found"}, status=404)
        white_labelling = getattr(
            getattr(settings, "HORILLA_APPS", None) or {}, "WHITE_LABELLING", False
        )
        image_path = path.join(settings.STATIC_ROOT, "images/ui/sync-logo.png")
        company_name = "Sync"
        if white_labelling and hasattr(request.user, "employee_get") and request.user.employee_get:
            try:
                from base.models import Company

                hq = Company.objects.filter(hq=True).last()
                company = (
                    request.user.employee_get.get_company()
                    if request.user.employee_get.get_company()
                    else hq
                )
                if company:
                    company_name = company.company
                    image_path = path.join(settings.MEDIA_ROOT, company.icon.name)
            except Exception:
                pass
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
                <table align="center" width="600" cellpadding="0" cellspacing="0" border="0" style="border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
                    <tr>
                        <td align="center" bgcolor="#4CAF50" style="padding: 20px 0;">
                            <h1 style="color: #ffffff; margin: 0;">{company_name}</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px;">
                            <h3 style="color: #4CAF50;">Email tested successfully</h3>
                            <b><p style="font-size: 14px;">Hi,<br>
                                This email is being sent as part of mail server testing from {company_name}.</p></b>
                            <img src="cid:unique_image_id" alt="Test Image" style="width: 200px; height: auto; margin: 20px 0;">
                        </td>
                    </tr>
                    <tr>
                        <td bgcolor="#f0f0f0" style="padding: 10px; text-align: center;">
                            <p style="font-size: 12px; color: black;">&copy; {datetime.today().year} {company_name}</p>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        text_content = strip_tags(html_content)
        email_backend = ConfiguredEmailBackend()
        email_backend.configuration = config
        try:
            msg = EmailMultiAlternatives(
                _("Test mail from Horilla"),
                text_content,
                email_backend.dynamic_from_email_with_display_name,
                [to_email],
                connection=email_backend,
            )
            msg.attach_alternative(html_content, "text/html")
            if path.exists(image_path):
                with open(image_path, "rb") as img:
                    msg_img = MIMEImage(img.read())
                    msg_img.add_header("Content-ID", "<unique_image_id>")
                    msg.attach(msg_img)
            msg.send()
        except Exception as e:
            return Response(
                {"error": " ".join([_("Something went wrong :"), str(e)])},
                status=400,
            )
        return Response({"message": "Mail sent successfully"}, status=200)


class MailServerReplacePrimaryView(APIView):
    """Set the given server as primary and delete the current primary (matches Django replace_primary_mail)."""

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("base.change_dynamicemailconfiguration"))
    def post(self, request):
        from base.models import DynamicEmailConfiguration

        replace_id = request.data.get("id") or request.data.get("replace_mail")
        if not replace_id:
            return Response({"error": "id or replace_mail is required"}, status=400)
        new_primary = DynamicEmailConfiguration.objects.filter(id=replace_id).first()
        if not new_primary:
            return Response({"error": "Mail server not found"}, status=404)
        current = DynamicEmailConfiguration.objects.filter(is_primary=True).first()
        if current:
            current.delete()
        new_primary.is_primary = True
        new_primary.save()
        return Response(
            {"message": "Primary Mail server configuration replaced", "server": _mail_server_payload(new_primary)},
            status=200,
        )


# ========== Gdrive Backup (horilla_backup) ==========


def _gdrive_backup_payload(obj):
    """Build response payload for GoogleDriveBackup (no file content)."""
    return {
        "id": obj.id,
        "gdrive_folder_id": obj.gdrive_folder_id or "",
        "backup_db": obj.backup_db,
        "backup_media": obj.backup_media,
        "interval": obj.interval,
        "fixed": obj.fixed,
        "seconds": obj.seconds,
        "hour": obj.hour,
        "minute": obj.minute,
        "active": obj.active,
    }


class GdriveBackupAPIView(APIView):
    """GET current gdrive backup config (if any). POST create or update (multipart). Only for PostgreSQL."""

    permission_classes = [IsAuthenticated]

    def _postgres_only(self):
        from django.db import connection

        if connection.vendor != "postgresql":
            return False
        return True

    @method_decorator(permission_required("backup.add_localbackup"))
    def get(self, request):
        if not self._postgres_only():
            return Response(
                {"error": "Gdrive backup is only available for PostgreSQL."},
                status=404,
            )
        try:
            from horilla_backup.models import GoogleDriveBackup

            obj = GoogleDriveBackup.objects.first()
        except Exception:
            obj = None
        if not obj:
            return Response({"show": False, "active": False}, status=200)
        payload = _gdrive_backup_payload(obj)
        payload["show"] = True
        return Response(payload, status=200)

    @method_decorator(permission_required("backup.add_localbackup"))
    def post(self, request):
        if not self._postgres_only():
            return Response(
                {"error": "Gdrive backup is only available for PostgreSQL."},
                status=404,
            )
        from horilla_backup.forms import GdriveBackupSetupForm
        from horilla_backup.models import GoogleDriveBackup
        from horilla_backup.scheduler import stop_gdrive_backup_job

        instance = GoogleDriveBackup.objects.first()
        data = request.POST.copy() if request.POST else {}
        files = request.FILES
        if instance and "service_account_file" not in files:
            data.pop("service_account_file", None)
            for key in ("gdrive_folder_id", "backup_db", "backup_media", "interval", "fixed", "seconds", "hour", "minute"):
                if key in data:
                    val = data[key]
                    if key in ("backup_db", "backup_media", "interval", "fixed"):
                        setattr(instance, key, val in (True, "true", "True", "1", 1))
                    elif key in ("seconds", "hour", "minute"):
                        try:
                            setattr(instance, key, int(val) if val not in (None, "") else None)
                        except (TypeError, ValueError):
                            setattr(instance, key, None)
                    else:
                        setattr(instance, key, val or "")
            if not instance.interval:
                instance.seconds = None
            if not instance.fixed:
                instance.hour = None
                instance.minute = None
            instance.active = False
            instance.save()
            stop_gdrive_backup_job()
            return Response(
                {"message": "gdrive backup automation setup updated.", "config": _gdrive_backup_payload(instance)},
                status=200,
            )
        form = GdriveBackupSetupForm(data, files=files, instance=instance)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.active = False
            obj.save()
            stop_gdrive_backup_job()
            return Response(
                {"message": "gdrive backup automation setup Created." if not instance else "gdrive backup automation setup updated.", "config": _gdrive_backup_payload(obj)},
                status=201 if not instance else 200,
            )
        return Response(form.errors, status=400)


class GdriveBackupStartStopView(APIView):
    """Toggle gdrive backup active and start/stop the job."""

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("backup.change_localbackup"))
    def post(self, request):
        from django.db import connection

        if connection.vendor != "postgresql":
            return Response(
                {"error": "Gdrive backup is only available for PostgreSQL."},
                status=404,
            )
        try:
            from horilla_backup.models import GoogleDriveBackup
            from horilla_backup.scheduler import start_gdrive_backup_job, stop_gdrive_backup_job

            obj = GoogleDriveBackup.objects.first()
        except Exception:
            return Response({"error": "No gdrive backup configured."}, status=400)
        if not obj:
            return Response({"error": "No gdrive backup configured."}, status=400)
        if obj.active:
            obj.active = False
            stop_gdrive_backup_job()
            message = "Gdrive Backup Automation Stopped Successfully."
        else:
            obj.active = True
            start_gdrive_backup_job()
            message = "Gdrive Backup Automation Started Successfully."
        obj.save()
        return Response({"message": message, "active": obj.active}, status=200)


class GdriveBackupDeleteView(APIView):
    """Delete gdrive backup config and stop the job."""

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("backup.delete_localbackup"))
    def post(self, request):
        from django.db import connection

        if connection.vendor != "postgresql":
            return Response(
                {"error": "Gdrive backup is only available for PostgreSQL."},
                status=404,
            )
        try:
            from horilla_backup.models import GoogleDriveBackup
            from horilla_backup.scheduler import stop_gdrive_backup_job

            obj = GoogleDriveBackup.objects.first()
        except Exception:
            return Response(status=204)
        if obj:
            obj.delete()
            stop_gdrive_backup_job()
        return Response(
            {"message": "Gdrive Backup Automation Removed Successfully."},
            status=200,
        )


class EmployeeWidgetFilterAPIView(APIView):
    """GET: Return filtered employee IDs and employee list for widget selection modal."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from employee.filters import EmployeeFilter
        from employee.models import Employee

        # Apply filters using EmployeeFilter
        filter_qs = EmployeeFilter(data=request.query_params, queryset=Employee.objects.all()).qs
        
        # Get IDs (for filtering existing table rows)
        ids = list(filter_qs.values_list("id", flat=True))
        
        # Get paginated employee list for display
        page = int(request.query_params.get("page", 1))
        page_size = min(int(request.query_params.get("page_size", 20)), 100)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = filter_qs[start:end]
        
        employees_list = []
        for emp in paginated:
            employees_list.append({
                "id": emp.id,
                "employee_first_name": getattr(emp, "employee_first_name", "") or "",
                "employee_last_name": getattr(emp, "employee_last_name", "") or "",
                "badge_id": getattr(emp, "badge_id", "") or "",
                "employee_id": getattr(emp, "badge_id", "") or "",
                "avatar": getattr(emp, "get_avatar", lambda: "")(),
                "full_name": emp.get_full_name() if hasattr(emp, "get_full_name") else f"{getattr(emp, 'employee_first_name', '')} {getattr(emp, 'employee_last_name', '')}".strip(),
            })
        
        total_count = filter_qs.count()
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1
        
        return Response({
            "ids": ids,
            "results": employees_list,
            "count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }, status=200)


class EmployeePermissionsListAPIView(APIView):
    """GET: Return list of employees who have assigned permissions."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from employee.models import Employee
        from rest_framework.pagination import PageNumberPagination

        # Filter employees who have permissions assigned
        employees_qs = Employee.objects.filter(
            employee_user_id__user_permissions__isnull=False
        ).distinct()
        
        # Apply search if provided
        search = request.query_params.get("search", "")
        if search:
            employees_qs = employees_qs.filter(
                Q(employee_first_name__icontains=search)
                | Q(employee_last_name__icontains=search)
                | Q(badge_id__icontains=search)
            )
        
        # Paginate
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get("page_size", 20))
        page = paginator.paginate_queryset(employees_qs, request)
        
        employees_list = []
        for emp in page:
            work_info = getattr(emp, "employee_work_info", None)
            employees_list.append({
                "id": emp.id,
                "employee_first_name": getattr(emp, "employee_first_name", "") or "",
                "employee_last_name": getattr(emp, "employee_last_name", "") or "",
                "badge_id": getattr(emp, "badge_id", "") or "",
                "avatar": getattr(emp, "get_avatar", lambda: "")(),
                "full_name": emp.get_full_name() if hasattr(emp, "get_full_name") else f"{getattr(emp, 'employee_first_name', '')} {getattr(emp, 'employee_last_name', '')}".strip(),
                "job_role": work_info.job_role_id.job_role if work_info and work_info.job_role_id else "",
                "job_position": str(work_info.job_position_id) if work_info and work_info.job_position_id else "",
                "department": str(work_info.department_id) if work_info and work_info.department_id else "",
                "work_info_text": f"{work_info.job_role_id.job_role if work_info and work_info.job_role_id else ''} | {str(work_info.job_position_id) if work_info and work_info.job_position_id else ''} | {str(work_info.department_id) if work_info and work_info.department_id else ''}".strip(" |"),
            })
        
        return paginator.get_paginated_response(employees_list)
