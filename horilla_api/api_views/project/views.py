import calendar
import datetime

import pandas as pd
from django.db.models import ProtectedError, Q
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from project.filters import ProjectFilter, TaskAllFilter, TimeSheetFilter
from project.models import Employee, Project, ProjectStage, Task, TimeSheet

from ...api_methods.base.methods import groupby_queryset
from ...api_serializers.project.serializers import (
    ProjectSerializer,
    ProjectStageSerializer,
    TaskSerializer,
    TimeSheetSerializer,
)


def _get_effective_company_id(request):
    """Resolve company ID for filtering (query param or logged-in user's company)."""
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


def create_crud_view(model_class, serializer_class, model_name):
    """Helper function to create CRUD views"""
    class CRUDView(APIView):
        permission_classes = [IsAuthenticated]

        def get(self, request, pk=None):
            if pk:
                try:
                    obj = model_class.objects.get(pk=pk)
                    serializer = serializer_class(obj)
                    return Response(serializer.data, status=200)
                except model_class.DoesNotExist:
                    return Response(
                        {"error": f"{model_name} not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            paginator = PageNumberPagination()
            queryset = model_class.objects.all()
            page = paginator.paginate_queryset(queryset, request)
            serializer = serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        def post(self, request):
            serializer = serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        def put(self, request, pk):
            try:
                obj = model_class.objects.get(pk=pk)
                serializer = serializer_class(obj, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=200)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except model_class.DoesNotExist:
                return Response(
                    {"error": f"{model_name} not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        def delete(self, request, pk):
            try:
                obj = model_class.objects.get(pk=pk)
                obj.delete()
                return Response(
                    {"message": f"{model_name} deleted successfully"},
                    status=status.HTTP_200_OK,
                )
            except model_class.DoesNotExist:
                return Response(
                    {"error": f"{model_name} not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except ProtectedError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return CRUDView


ProjectBaseAPIView = create_crud_view(Project, ProjectSerializer, "Project")
ProjectStageAPIView = create_crud_view(
    ProjectStage, ProjectStageSerializer, "ProjectStage"
)
TIMESHEET_GROUPBY_FIELDS = [
    "employee_id",
    "project_id",
    "date",
    "status",
    "employee_id__employee_work_info__reporting_manager_id",
    "employee_id__employee_work_info__department_id",
    "employee_id__employee_work_info__job_position_id",
    "employee_id__employee_work_info__employee_type_id",
    "employee_id__employee_work_info__company_id",
]


class TimeSheetAPIView(APIView):
    """
    TimeSheet CRUD API with filtering and optional group-by, aligned with TimeSheetFilter.
    List: GET /api/v1/project/timesheets/ with query params employee_id, project_id,
          task_id, date, status, start_from, end_till, search, groupby_field.
    Detail: GET/PUT/DELETE /api/v1/project/timesheets/<pk>/.
    """

    permission_classes = [IsAuthenticated]
    filterset_class = TimeSheetFilter

    def get(self, request, pk=None):
        if pk is not None:
            try:
                obj = TimeSheet.objects.get(pk=pk)
            except TimeSheet.DoesNotExist:
                return Response(
                    {"error": "TimeSheet not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            company_id = _get_effective_company_id(request)
            if company_id is not None:
                project_company_match = obj.project_id and obj.project_id.company_id and obj.project_id.company_id.id == company_id
                employee_company_match = (
                    obj.employee_id and
                    hasattr(obj.employee_id, 'employee_work_info') and
                    obj.employee_id.employee_work_info and
                    obj.employee_id.employee_work_info.company_id and
                    obj.employee_id.employee_work_info.company_id.id == company_id
                )
                if not (project_company_match or employee_company_match):
                    return Response(
                        {"error": "TimeSheet not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            serializer = TimeSheetSerializer(obj)
            return Response(serializer.data, status=status.HTTP_200_OK)

        queryset = TimeSheet.objects.all().order_by("-id")
        company_id = _get_effective_company_id(request)
        if company_id is not None:
            # Filter by project's company OR employee's company (timesheet can be scoped via either)
            queryset = queryset.filter(
                Q(project_id__company_id=company_id) |
                Q(employee_id__employee_work_info__company_id=company_id)
            )
        filterset = self.filterset_class(request.GET, queryset=queryset)
        field_name = request.GET.get("groupby_field")
        if field_name and field_name in TIMESHEET_GROUPBY_FIELDS:
            url = request.build_absolute_uri()
            return groupby_queryset(request, url, field_name, filterset.qs)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(filterset.qs, request)
        serializer = TimeSheetSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = TimeSheetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            obj = TimeSheet.objects.get(pk=pk)
        except TimeSheet.DoesNotExist:
            return Response(
                {"error": "TimeSheet not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TimeSheetSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            obj = TimeSheet.objects.get(pk=pk)
            obj.delete()
            return Response(
                {"message": "TimeSheet deleted successfully"},
                status=status.HTTP_200_OK,
            )
        except TimeSheet.DoesNotExist:
            return Response(
                {"error": "TimeSheet not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ProtectedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TaskAPIView(APIView):
    """
    Task CRUD API with filtering and optional group-by, aligned with TaskAllFilter.
    List: GET /api/v1/project/tasks/ with query params project, stage, status,
          task_managers, task_members, end_till, groupby_field (project|stage|status).
    Detail: GET/PUT/DELETE /api/v1/project/tasks/<pk>/.
    """

    permission_classes = [IsAuthenticated]
    filterset_class = TaskAllFilter

    def get(self, request, pk=None):
        if pk is not None:
            try:
                obj = Task.objects.get(pk=pk)
            except Task.DoesNotExist:
                return Response(
                    {"error": "Task not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            company_id = _get_effective_company_id(request)
            if company_id is not None and (not obj.project or not obj.project.company_id or obj.project.company_id.id != company_id):
                return Response(
                    {"error": "Task not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = TaskSerializer(obj)
            return Response(serializer.data, status=status.HTTP_200_OK)

        queryset = Task.objects.all().order_by("-id")
        company_id = _get_effective_company_id(request)
        if company_id is not None:
            queryset = queryset.filter(project__company_id=company_id)
        filterset = self.filterset_class(request.GET, queryset=queryset)
        field_name = request.GET.get("groupby_field")
        if field_name and field_name in ("project", "stage", "status"):
            url = request.build_absolute_uri()
            return groupby_queryset(request, url, field_name, filterset.qs)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(filterset.qs, request)
        serializer = TaskSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            obj = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TaskSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            obj = Task.objects.get(pk=pk)
            obj.delete()
            return Response(
                {"message": "Task deleted successfully"},
                status=status.HTTP_200_OK,
            )
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ProtectedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProjectAPIView(APIView):
    """
    Project CRUD API with filtering and optional group-by, aligned with ProjectFilter.
    Enforces strict multi-tenant data isolation: employees only see projects from their company
    or projects where they are manager/member. Superusers see all projects.
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProjectFilter

    def _get_filtered_queryset(self, request):
        """
        Returns queryset filtered by role and company membership.
        - Superusers: respect navbar company switcher (selected_company in session).
          If selected_company == "all" -> all projects; if specific company ID -> only that company's projects.
        - Regular employees: projects from their company OR projects where they are manager/member (unchanged).
        """
        queryset = Project.objects.select_related("company_id").prefetch_related(
            "managers", "members"
        ).order_by("-id")

        # Superusers: scope by selected company from navbar
        # Check both query param (React frontend) and session (Django UI)
        if request.user.is_superuser:
            # Priority 1: Query parameter (React frontend sends companyId as company_id)
            company_id_param = request.query_params.get("company_id")
            if company_id_param and str(company_id_param).strip().lower() not in ("", "all"):
                try:
                    cid = int(company_id_param)
                    queryset = queryset.filter(company_id_id=cid)
                    return queryset
                except (TypeError, ValueError):
                    pass  # invalid value: fallback to session
            
            # Priority 2: Session (Django UI navbar switcher)
            selected_company = request.session.get("selected_company")
            if selected_company and selected_company != "all":
                try:
                    cid = int(selected_company)
                    queryset = queryset.filter(company_id_id=cid)
                except (TypeError, ValueError):
                    pass  # invalid value: show all
            
            # If both are "all" or missing -> return all projects (unchanged queryset)
            return queryset

        # Non-superuser: existing employee company + manager/member filtering (unchanged)
        employee = getattr(request.user, "employee_get", None)
        if not employee:
            return Project.objects.none()

        company = None
        if hasattr(employee, "employee_work_info") and employee.employee_work_info:
            company = employee.employee_work_info.company_id

        filter_conditions = Q()
        if company:
            filter_conditions |= Q(company_id=company)
        filter_conditions |= Q(managers=employee) | Q(members=employee)

        return queryset.filter(filter_conditions).distinct()

    def get(self, request, pk=None):
        # Detail view
        if pk is not None:
            try:
                obj = Project.objects.select_related("company_id").prefetch_related(
                    "managers", "members"
                ).get(pk=pk)
            except Project.DoesNotExist:
                return Response(
                    {"error": "Project not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            
            # Check access: superuser OR company match OR manager/member
            has_access = False
            if request.user.is_superuser:
                has_access = True
            else:
                employee = getattr(request.user, "employee_get", None)
                if employee:
                    company = None
                    if hasattr(employee, "employee_work_info") and employee.employee_work_info:
                        company = employee.employee_work_info.company_id
                    
                    if company and obj.company_id and obj.company_id.id == company.id:
                        has_access = True
                    elif obj.managers.filter(id=employee.id).exists() or obj.members.filter(id=employee.id).exists():
                        has_access = True
            
            if not has_access:
                return Response(
                    {"error": "Project not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            
            serializer = ProjectSerializer(obj)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # List view with filters and optional groupby_field
        queryset = self._get_filtered_queryset(request)
        
        # Create a mutable copy of request.GET and remove company_id to prevent ProjectFilter
        # from applying additional filtering that conflicts with our role-based filtering
        filter_params = request.GET.copy()
        if 'company_id' in filter_params:
            filter_params.pop('company_id')
        
        filterset = self.filterset_class(filter_params, queryset=queryset)
        field_name = request.GET.get("groupby_field")
        if field_name:
            url = request.build_absolute_uri()
            return groupby_queryset(request, url, field_name, filterset.qs)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(filterset.qs, request)
        serializer = ProjectSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        # Auto-set company_id if not provided
        if "company_id" not in data or not data.get("company_id"):
            company_id = _get_effective_company_id(request)
            if company_id is not None:
                data["company_id"] = company_id
        serializer = ProjectSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            obj = Project.objects.select_related("company_id").prefetch_related(
                "managers", "members"
            ).get(pk=pk)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check access: superuser OR company match OR manager/member
        has_access = False
        if request.user.is_superuser:
            has_access = True
        else:
            employee = getattr(request.user, "employee_get", None)
            if employee:
                company = None
                if hasattr(employee, "employee_work_info") and employee.employee_work_info:
                    company = employee.employee_work_info.company_id
                
                if company and obj.company_id and obj.company_id.id == company.id:
                    has_access = True
                elif obj.managers.filter(id=employee.id).exists() or obj.members.filter(id=employee.id).exists():
                    has_access = True
        
        if not has_access:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = ProjectSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            obj = Project.objects.select_related("company_id").prefetch_related(
                "managers", "members"
            ).get(pk=pk)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check access: superuser OR company match OR manager/member
        has_access = False
        if request.user.is_superuser:
            has_access = True
        else:
            employee = getattr(request.user, "employee_get", None)
            if employee:
                company = None
                if hasattr(employee, "employee_work_info") and employee.employee_work_info:
                    company = employee.employee_work_info.company_id
                
                if company and obj.company_id and obj.company_id.id == company.id:
                    has_access = True
                elif obj.managers.filter(id=employee.id).exists() or obj.members.filter(id=employee.id).exists():
                    has_access = True
        
        if not has_access:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        try:
            obj.delete()
            return Response(
                {"message": "Project deleted successfully"},
                status=status.HTTP_200_OK,
            )
        except ProtectedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProjectImportAPIView(APIView):
    """
    JWT-authenticated API for Project import/template.
    GET  -> returns empty Excel template (same columns as classic project_import view)
    POST -> accepts Excel file, attempts to create/update projects, and
            returns either a simple success message or an Excel file with row-level errors.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Create empty template with the same columns as the legacy view
        data_frame = pd.DataFrame(
            columns=[
                "Title",
                "Manager Badge id",
                "Member Badge id",
                "Status",
                "Start Date",
                "End Date",
                "Description",
            ]
        )
        response = HttpResponse(content_type="application/ms-excel")
        response[
            "Content-Disposition"
        ] = 'attachment; filename="project_template.xlsx"'
        data_frame.to_excel(response, index=False)
        return response

    def post(self, request):
        """
        Accepts an Excel file and attempts to import projects.
        On success: returns a small text blob ("Imported successfully").
        On validation errors: returns an Excel file with error columns.
        """
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"detail": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data_frame = pd.read_excel(uploaded_file)
        except Exception as exc:
            return Response(
                {"detail": f"Could not read Excel file: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from project.views import convert_nan  # reuse existing helper

        project_dicts = data_frame.to_dict("records")
        error_lists = []

        for project in project_dicts:
            try:
                title = project.get("Title")
                manager_badge_id = convert_nan("Manager Badge id", project)
                member_badge_id = convert_nan("Member Badge id", project)
                status_value = project.get("Status")
                start_date = project.get("Start Date")
                end_date = project.get("End Date")
                description = project.get("Description")

                is_save = True

                managers = []
                if manager_badge_id:
                    ids = manager_badge_id.split(",")
                    error_ids = []
                    for _id in ids:
                        if Employee.objects.filter(badge_id=_id).exists():
                            employee = Employee.objects.filter(badge_id=_id).first()
                            managers.append(employee)
                        else:
                            error_ids.append(_id)
                            is_save = False
                    if error_ids:
                        ids = ",".join(map(str, error_ids))
                        project["Manager error"] = f"{ids} - This id not exists"

                members = []
                if member_badge_id:
                    ids = member_badge_id.split(",")
                    error_ids = []
                    for _id in ids:
                        if Employee.objects.filter(badge_id=_id).exists():
                            employee = Employee.objects.filter(badge_id=_id).first()
                            members.append(employee)
                        else:
                            error_ids.append(_id)
                            is_save = False
                    if error_ids:
                        ids = ",".join(map(str, error_ids))
                        project["Member error"] = f"{ids} - This id not exists"

                if status_value:
                    if status_value not in [stat for stat, _ in Project.PROJECT_STATUS]:
                        project["Status error"] = (
                            f"{status_value} not available in Project status"
                        )
                        is_save = False
                else:
                    project["Status error"] = "Status is a required field"
                    is_save = False

                date_format = "%Y-%m-%d"
                if start_date is not None and not pd.isna(start_date):
                    try:
                        _ = datetime.datetime.strptime(
                            start_date.strftime("%Y-%m-%d"), date_format
                        )
                    except Exception:
                        project["Start date error"] = (
                            "Date must be in 'YYYY-MM-DD' format"
                        )
                        is_save = False
                else:
                    project["Start date error"] = "Start date is a required field"
                    is_save = False

                if end_date is not None and not pd.isna(end_date):
                    try:
                        _ = datetime.datetime.strptime(
                            end_date.strftime("%Y-%m-%d"), date_format
                        )
                        if start_date and end_date < start_date:
                            project["End date error"] = (
                                "End date cannot be less than start date"
                            )
                            is_save = False
                    except Exception:
                        project["End date error"] = (
                            "Date must be in 'YYYY-MM-DD' format"
                        )
                        is_save = False

                if not title:
                    project["Title error"] = "Title is a required field"
                    is_save = False

                if is_save:
                    project_obj, _ = Project.objects.get_or_create(title=title)
                    project_obj.status = status_value
                    project_obj.start_date = (
                        start_date.date() if hasattr(start_date, "date") else start_date
                    )
                    project_obj.end_date = (
                        end_date.date() if hasattr(end_date, "date") else end_date
                    )
                    project_obj.description = description
                    project_obj.save()
                    if managers:
                        project_obj.managers.set(managers)
                    if members:
                        project_obj.members.set(members)
                else:
                    error_lists.append(project)
            except Exception as error:
                project["error"] = str(error)
                error_lists.append(project)

        if error_lists:
            error_frame = pd.DataFrame(error_lists)
            response = HttpResponse(content_type="application/ms-excel")
            response[
                "Content-Disposition"
            ] = 'attachment; filename="ImportError.xlsx"'
            error_frame.to_excel(response, index=False)
            return response

        # success case
        return HttpResponse(
            "Imported successfully",
            content_type="text/plain",
        )


class ProjectExportAPIView(APIView):
    """
    JWT-authenticated bulk export for projects.
    Expects POST with "ids" as JSON array, returns Excel file just like the classic view.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        import json

        ids_raw = request.data.get("ids") or request.POST.get("ids")
        if not ids_raw:
            return Response(
                {"detail": "No project IDs provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            ids = json.loads(ids_raw)
        except Exception as exc:
            return Response(
                {"detail": f"Invalid ids payload: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data_list = []
        headers = [
            "Title",
            "Managers",
            "Members",
            "Status",
            "Start Date",
            "End Date",
            "Description",
        ]

        for project_id in ids:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                continue
            data = {
                "Title": f"{project.title}",
                "Managers": ",".join(
                    [
                        f"{m.employee_first_name} {m.employee_last_name}"
                        for m in project.managers.all()
                    ]
                )
                if project.managers.exists()
                else "",
                "Members": ",".join(
                    [
                        f"{m.employee_first_name} {m.employee_last_name}"
                        for m in project.members.all()
                    ]
                )
                if project.members.exists()
                else "",
                "Status": f"{project.status}",
                "Start Date": project.start_date.strftime("%Y-%m-%d")
                if project.start_date
                else "",
                "End Date": project.end_date.strftime("%Y-%m-%d")
                if project.end_date
                else "",
                "Description": f"{project.description}",
            }
            data_list.append(data)

        data_frame = pd.DataFrame(data_list, columns=headers)

        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = 'attachment; filename="project details.xlsx"'
        writer = pd.ExcelWriter(response, engine="xlsxwriter")
        data_frame.to_excel(
            writer,
            sheet_name="Project details",
            index=False,
            startrow=3,
        )
        workbook = writer.book
        worksheet = writer.sheets["Project details"]
        max_columns = len(headers)
        heading_format = workbook.add_format(
            {
                "bg_color": "#ffd0cc",
                "bold": True,
                "font_size": 14,
                "align": "center",
                "valign": "vcenter",
                "font_size": 20,
            }
        )
        header_format = workbook.add_format(
            {
                "bg_color": "#EDF1FF",
                "bold": True,
                "text_wrap": True,
                "font_size": 12,
                "align": "center",
                "border": 1,
            }
        )
        worksheet.set_row(0, 30)
        worksheet.merge_range(
            0,
            0,
            0,
            max_columns - 1,
            "Project details ",
            heading_format,
        )
        for col_num, value in enumerate(data_frame.columns.values):
            worksheet.write(3, col_num, value, header_format)
            col_letter = chr(65 + col_num)
            header_width = max(
                len(str(value)) + 2,
                len(data_frame[value].astype(str).max()) + 2,
            )
            worksheet.set_column(f"{col_letter}:{col_letter}", header_width)

        writer.close()
        return response


class TasksMyAPIView(APIView):
    """
    Returns tasks where the current user's employee is task_manager or task_member.
    Supports TaskAllFilter fields and groupby_field (project, stage, status).
    """
    permission_classes = [IsAuthenticated]
    filterset_class = TaskAllFilter

    def get(self, request):
        employee = getattr(request.user, "employee_get", None)
        if not employee:
            queryset = Task.objects.none()
        else:
            queryset = Task.objects.filter(
                Q(task_managers=employee) | Q(task_members=employee)
            ).distinct()
        company_id = _get_effective_company_id(request)
        if company_id is not None:
            queryset = queryset.filter(project__company_id=company_id)
        queryset = queryset.order_by("-id")
        filterset = self.filterset_class(request.GET, queryset=queryset)
        field_name = request.GET.get("groupby_field")
        if field_name and field_name in ("project", "stage", "status"):
            url = request.build_absolute_uri()
            return groupby_queryset(request, url, field_name, filterset.qs)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(filterset.qs, request)
        serializer = TaskSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProjectsDueInMonthAPIView(APIView):
    """
    Returns projects with end_date in the current month, excluding expired.
    Aligns with dashboard projects-due-in-this-month logic.
    Enforces strict multi-tenant data isolation.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = datetime.date.today()
        first_day = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        last_day_of_month = today.replace(day=last_day)
        
        # Base queryset with date filter
        queryset = Project.objects.select_related("company_id").prefetch_related(
            "managers", "members"
        ).filter(
            Q(end_date__gte=first_day) & Q(end_date__lte=last_day_of_month)
        ).exclude(status="expired")
        
        # Apply role-based filtering
        if request.user.is_superuser:
            # Superusers see all projects
            pass
        else:
            employee = getattr(request.user, "employee_get", None)
            if not employee:
                queryset = Project.objects.none()
            else:
                company = None
                if hasattr(employee, "employee_work_info") and employee.employee_work_info:
                    company = employee.employee_work_info.company_id
                
                filter_conditions = Q()
                if company:
                    filter_conditions |= Q(company_id=company)
                filter_conditions |= Q(managers=employee) | Q(members=employee)
                queryset = queryset.filter(filter_conditions).distinct()
        
        queryset = queryset.order_by("end_date")
        serializer = ProjectSerializer(queryset, many=True)
        return Response(serializer.data, status=200)

