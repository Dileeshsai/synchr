import io
import logging
import threading

import io
import logging
import mimetypes
import pandas as pd
import threading
from django.db.models import ProtectedError, Q
from django.http import Http404, HttpResponse, FileResponse
from django.template import Context, Template
from django.core.mail import EmailMessage
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


from base.models import JobPosition
from base.views import generate_error_report
from employee.filters import (
    DisciplinaryActionFilter,
    DocumentRequestFilter,
    EmployeeFilter,
)
from employee.methods.methods import (
    bulk_create_department_import,
    bulk_create_employee_import,
    bulk_create_employee_types,
    bulk_create_job_position_import,
    bulk_create_job_role_import,
    bulk_create_shifts,
    bulk_create_user_import,
    bulk_create_work_info_import,
    bulk_create_work_types,
    error_data_template,
    process_employee_records,
    set_initial_password,
    valid_import_file_headers,
)
from employee.models import (
    Actiontype,
    DisciplinaryAction,
    Employee,
    EmployeeBankDetails,
    EmployeeType,
    EmployeeTag,
    EmployeeWorkInformation,
    Policy,
    PolicyMultipleFile,
)
from base.methods import filtersubordinatesemployeemodel
from employee.views import work_info_export, work_info_import
from horilla.decorators import owner_can_enter
from horilla_api.api_decorators.base.decorators import permission_required
from horilla_api.api_methods.employee.methods import get_next_badge_id
from horilla_documents.models import Document, DocumentRequest
from notifications.signals import notify

from ...api_decorators.base.decorators import (
    manager_or_owner_permission_required,
    manager_permission_required,
)
from ...api_decorators.employee.decorators import or_condition
from ...api_methods.base.methods import groupby_queryset, permission_based_queryset
from ...api_serializers.employee.serializers import (
    ActiontypeSerializer,
    DisciplinaryActionSerializer,
    DocumentRequestSerializer,
    DocumentSerializer,
    EmployeeBankDetailsSerializer,
    EmployeeListSerializer,
    EmployeeSelectorSerializer,
    EmployeeSerializer,
    EmployeeTypeSerializer,
    EmployeeTagSerializer,
    EmployeeWorkInformationSerializer,
    PolicySerializer,
)


logger = logging.getLogger(__name__)


def permission_check(request, perm):
    return request.user.has_perm(perm)


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


class EmployeeTypeAPIView(APIView):
    """
    CRUD API for employee types.

    Methods:
        GET  /employee-type/           → list
        GET  /employee-type/<pk>/      → detail
        POST /employee-type/           → create
        PUT  /employee-type/<pk>/      → update
        DELETE /employee-type/<pk>/    → delete
    """

    serializer_class = EmployeeTypeSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            employee_type = object_check(EmployeeType, pk)
            if employee_type is None:
                return Response({"error": "EmployeeType not found"}, status=404)
            serializer = self.serializer_class(employee_type)
            return Response(serializer.data, status=200)
        employee_type = EmployeeType.objects.all()
        serializer = self.serializer_class(employee_type, many=True)
        return Response(serializer.data, status=200)

    @method_decorator(permission_required("base.add_employeetype"), name="dispatch")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.change_employeetype"), name="dispatch")
    def put(self, request, pk):
        employee_type = object_check(EmployeeType, pk)
        if employee_type is None:
            return Response({"error": "EmployeeType not found"}, status=404)
        serializer = self.serializer_class(employee_type, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("base.delete_employeetype"), name="dispatch")
    def delete(self, request, pk):
        employee_type = object_check(EmployeeType, pk)
        if employee_type is None:
            return Response({"error": "EmployeeType not found"}, status=404)
        response, status_code = object_delete(EmployeeType, pk)
        return Response(response, status=status_code)


class EmployeeTagAPIView(APIView):
    """
    CRUD API for employee tags.

    Methods:
        GET  /employee-tag/           → list
        GET  /employee-tag/<pk>/      → detail
        POST /employee-tag/           → create
        PUT  /employee-tag/<pk>/      → update
        DELETE /employee-tag/<pk>/    → delete
    """

    serializer_class = EmployeeTagSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            tag = object_check(EmployeeTag, pk)
            if tag is None:
                return Response({"error": "EmployeeTag not found"}, status=404)
            serializer = self.serializer_class(tag)
            return Response(serializer.data, status=200)
        tags = EmployeeTag.objects.all()
        serializer = self.serializer_class(tags, many=True)
        return Response(serializer.data, status=200)

    @method_decorator(permission_required("employee.add_employeetag"), name="dispatch")
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @method_decorator(
        permission_required("employee.change_employeetag"), name="dispatch"
    )
    def put(self, request, pk):
        tag = object_check(EmployeeTag, pk)
        if tag is None:
            return Response({"error": "EmployeeTag not found"}, status=404)
        serializer = self.serializer_class(tag, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(
        permission_required("employee.delete_employeetag"), name="dispatch"
    )
    def delete(self, request, pk):
        tag = object_check(EmployeeTag, pk)
        if tag is None:
            return Response({"error": "EmployeeTag not found"}, status=404)
        response, status_code = object_delete(EmployeeTag, pk)
        return Response(response, status=status_code)


class EmployeeAPIView(APIView):
    """
    Handles CRUD operations for employees.

    Methods:
        get(request, pk=None):
            - Retrieves a single employee by pk if provided.
            - Retrieves and filters all employees if pk is not provided.

        post(request):
            - Creates a new employee if the user has the 'employee.change_employee' permission.

        put(request, pk):
            - Updates an existing employee if the user is the employee, a manager, or has 'employee.change_employee' permission.

        delete(request, pk):
            - Deletes an employee if the user has the 'employee.delete_employee' permission.
    """

    filter_backends = [DjangoFilterBackend]
    filterset_class = EmployeeFilter
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            try:
                employee = Employee.objects.get(pk=pk)
            except Employee.DoesNotExist:
                return Response(
                    {"error": "Employee does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = EmployeeSerializer(employee)
            return Response(serializer.data)
        paginator = PageNumberPagination()
        # Apply is_active first (mirror Django UI): "False" = archived only, "True" = active only, missing = active only
        is_active_param = request.GET.get("is_active")
        if is_active_param is not None:
            is_active_lower = str(is_active_param).strip().lower()
            if is_active_lower == "false":
                employees_queryset = Employee.objects.filter(is_active=False)
            elif is_active_lower == "true":
                employees_queryset = Employee.objects.filter(is_active=True)
            else:
                employees_queryset = Employee.objects.all()
        else:
            employees_queryset = Employee.objects.filter(is_active=True)
        employees_filter_queryset = self.filterset_class(
            request.GET, queryset=employees_queryset
        ).qs
        if is_active_param is None:
            employees_filter_queryset = employees_filter_queryset.filter(is_active=True)
        # Align with backend UI: restrict to employees the user can see (permission/subordinates)
        employees_filter_queryset = filtersubordinatesemployeemodel(
            request, employees_filter_queryset, "employee.view_employee"
        )
        field_name = request.GET.get("groupby_field", None)
        if field_name:
            url = request.build_absolute_uri()
            return groupby_queryset(request, url, field_name, employees_filter_queryset)
        page = paginator.paginate_queryset(employees_filter_queryset, request)
        serializer = EmployeeSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @method_decorator(permission_required("employee.add_employee"))
    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @method_decorator(permission_required("employee.put_employee"))
    def put(self, request, pk):
        user = request.user
        employee = Employee.objects.get(pk=pk)
        if (
            employee
            in [user.employee_get, request.user.employee_get.get_reporting_manager()]
        ) or user.has_perm("employee.change_employee"):
            serializer = EmployeeSerializer(employee, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "You don't have permission"}, status=400)

    @method_decorator(permission_required("employee.delete_employee"))
    def delete(self, request, pk):
        try:
            employee = Employee.objects.get(pk=pk)
            employee.delete()
        except Employee.DoesNotExist:
            return Response(
                {"error": "Employee does not exist"}, status=status.HTTP_404_NOT_FOUND
            )
        except ProtectedError as e:
            return Response({"error": str(e)}, status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeListAPIView(APIView):
    """
    Retrieves a paginated list of employees with optional search functionality.

    Methods:
        get(request):
            - Returns a paginated list of employees.
            - Optionally filters employees based on a search query in the first or last name.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        paginator = PageNumberPagination()
        paginator.page_size = 13
        search = request.query_params.get("search", None)
        if search:
            employees_queryset = Employee.objects.filter(
                Q(employee_first_name__icontains=search)
                | Q(employee_last_name__icontains=search)
            )
        else:
            employees_queryset = Employee.objects.all()
        page = paginator.paginate_queryset(employees_queryset, request)
        serializer = EmployeeListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class EmployeeBankDetailsAPIView(APIView):
    """
    Manage employee bank details with CRUD operations.

    Methods:
        get(request, pk=None):
            - Retrieves bank details for a specific employee if `pk` is provided.
            - Returns a paginated list of all employee bank details if `pk` is not provided.

        post(request):
            - Creates a new bank detail entry for an employee.

        put(request, pk):
            - Updates existing bank details for an employee identified by `pk`.

        delete(request, pk):
            - Deletes bank details for an employee identified by `pk`.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = EmployeeBankDetails.objects.all()
        user = self.request.user
        # checking user level permissions
        perm = "base.view_employeebankdetails"
        queryset = permission_based_queryset(user, perm, queryset)
        return queryset
    
    def get(self, request, pk=None):
     if pk:
        # Detail view
        try:
            obj = EmployeeBankDetails.objects.get(pk=pk)
            serializer = EmployeeBankDetailsSerializer(obj)
            return Response(serializer.data)
        except EmployeeBankDetails.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
     else:
        # List view
        queryset = EmployeeBankDetails.objects.all()
        serializer = EmployeeBankDetailsSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EmployeeBankDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @manager_or_owner_permission_required(
        EmployeeBankDetails, "employee.add_employeebankdetails"
    )
    def put(self, request, pk):
        try:
            bank_detail = EmployeeBankDetails.objects.get(pk=pk)
        except EmployeeBankDetails.DoesNotExist:
            return Response(
                {"error": "Bank details do not exist"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmployeeBankDetailsSerializer(bank_detail, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @manager_permission_required("employee.change_employeebankdetails")
    def delete(self, request, pk):
        try:
            bank_detail = EmployeeBankDetails.objects.get(pk=pk)
            bank_detail.delete()
        except EmployeeBankDetails.DoesNotExist:
            return Response(
                {"error": "Bank details do not exist"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as E:
            return Response({"error": str(E)}, status=400)

        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeWorkInformationAPIView(APIView):
    """
    Manage employee work information with CRUD operations.

    Methods:
        get(request, pk):
            - Retrieves work information for a specific employee identified by `pk`.

        post(request):
            - Creates a new work information entry for an employee.

        put(request, pk):
            - Updates existing work information for an employee identified by `pk`.

        delete(request, pk):
            - Deletes work information for an employee identified by `pk`.
    """

    permission_classes = [IsAuthenticated]

    def get(self,request,pk=None):
        employee_id = request.GET.get("employee_id", None)
        reporting_manager_id = request.GET.get("reporting_manager_id", None)
        if pk:
            work_info = EmployeeWorkInformation.objects.get(pk=pk)
            if (
                request.user.employee_get
                in [work_info.employee_id, work_info.reporting_manager_id]
            ) or request.user.has_perm("employee.view_employeeworkinformation"):
                serializer = EmployeeWorkInformationSerializer(work_info)
                return Response(serializer.data, status=200)
            return Response({"message": "No permission"}, status=400)
        else:
            queryset = EmployeeWorkInformation.objects.all()
            if employee_id:
                queryset = queryset.filter(employee_id=employee_id)
            if reporting_manager_id:
                queryset = queryset.filter(reporting_manager_id=reporting_manager_id)
            serializer = EmployeeWorkInformationSerializer(queryset, many=True)
            return Response(serializer.data, status=200)

    @manager_permission_required("employee.add_employeeworkinformation")
    def post(self, request):
        serializer = EmployeeWorkInformationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @manager_permission_required("employee.change_employeeworkinformation")
    def put(self, request, pk):
        work_info = EmployeeWorkInformation.objects.get(pk=pk)
        if (
            request.user.employee_get == work_info.reporting_manager_id
            or request.user.has_perm("employee.change_employeeworkinformation")
        ):
            serializer = EmployeeWorkInformationSerializer(
                work_info, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "No permission"}, status=400)

    @method_decorator(
        permission_required("employee.delete_employeeworkinformation"), name="dispatch"
    )
    def delete(self, request, pk):
        try:
            work_info = EmployeeWorkInformation.objects.get(pk=pk)
        except EmployeeWorkInformation.DoesNotExist:
            raise Http404
        work_info.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeWorkInfoExportView(APIView):
    """
    Endpoint for exporting employee work information.

    Methods:
        get(request):
            - Exports work information data based on user permissions.
    """

    permission_classes = [IsAuthenticated]

    @manager_permission_required("employee.add_employeeworkinformation")
    def get(self, request):
        return work_info_export(request)


logger = logging.getLogger(__name__)


class EmployeeWorkInfoImportView(APIView):
    """
    Endpoint for importing employee work information.
    GET: returns HTML import page (Django UI).
    POST: accepts multipart file (field "file"), runs import, returns JSON.
    """

    permission_classes = [IsAuthenticated]

    @manager_permission_required("employee.add_employeeworkinformation")
    def get(self, request):
        # Keep GET behaviour for compatibility with existing Django template flow.
        from employee.views import work_info_import  # local import to avoid circulars

        return work_info_import(request)

    @manager_permission_required("employee.add_employee")
    def post(self, request):
        """
        Handle employee work info import from an uploaded file and return JSON.
        Mirrors the logic of employee.views.work_info_import but returns
        structured API responses instead of HTML.
        """
        upload = request.FILES.get("file")
        if not upload:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        file_extension = upload.name.split(".")[-1].lower()

        try:
            if file_extension == "csv":
                data_frame = pd.read_csv(upload)
            elif file_extension in ["xls", "xlsx"]:
                data_frame = pd.read_excel(upload)
            else:
                return Response(
                    {
                        "error": "Unsupported file format. "
                        "Please upload a CSV or Excel file."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            valid, error_message = valid_import_file_headers(data_frame)
            if not valid:
                return Response(
                    {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
                )

            success_list, error_list, created_count = process_employee_records(
                data_frame
            )

            if success_list:
                try:
                    users = bulk_create_user_import(success_list)
                    employees = bulk_create_employee_import(success_list)
                    bulk_create_department_import(success_list)
                    bulk_create_job_position_import(success_list)
                    bulk_create_job_role_import(success_list)
                    bulk_create_work_types(success_list)
                    bulk_create_shifts(success_list)
                    bulk_create_employee_types(success_list)
                    bulk_create_work_info_import(success_list)

                    thread = threading.Thread(
                        target=set_initial_password, args=(employees,)
                    )
                    thread.start()
                except Exception as e:
                    logger.error("Error during bulk create for import: %s", e)

            path_info = (
                generate_error_report(
                    error_list, error_data_template, "EmployeesImportError.xlsx"
                )
                if error_list
                else None
            )

            total_count = created_count + len(error_list)
            message = (
                f"Import complete: {created_count} created, {len(error_list)} errors."
            )

            return Response(
                {
                    "created_count": created_count,
                    "total_count": total_count,
                    "error_count": len(error_list),
                    "model": "Employees",
                    "error_report": path_info,
                    "message": message,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error("File import error: %s", e)
            return Response(
                {
                    "error": (
                        "Failed to read file. Please ensure it is a valid "
                        f"CSV or Excel file. : {e}"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class EmployeeWorkInfoImportTemplateView(APIView):
    """
    Endpoint for downloading employee work info import template (Excel).

    Methods:
        get(request):
            - Returns an Excel template file with required columns for employee import.
    """

    permission_classes = [IsAuthenticated]

    @manager_permission_required("employee.add_employee")
    def get(self, request):
        data_frame = pd.DataFrame(
            columns=[
                "Badge ID",
                "First Name",
                "Last Name",
                "Email",
                "Phone",
                "Gender",
                "Department",
                "Job Position",
                "Job Role",
                "Shift",
                "Work Type",
                "Reporting Manager",
                "Employee Type",
                "Location",
                "Date Joining",
                "Basic Salary",
                "Salary Hour",
                "Contract End Date",
                "Company",
            ]
        )
        buffer = io.BytesIO()
        data_frame.to_excel(buffer, index=False)
        buffer.seek(0)
        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="work_info_template.xlsx"'
        return response


class EmployeeBulkUpdateView(APIView):
    """
        Endpoint for bulk updating employee and work information.

        Permissions:
            - Requires authentication and "change_employee" permission.
    0
        Methods:
            put(request):
                - Updates multiple employees and their work information.
    """

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("employee.change_employee"), name="dispatch")
    def put(self, request):
        employee_ids = request.data.get("ids", [])
        employees = Employee.objects.filter(id__in=employee_ids)
        employee_work_info = EmployeeWorkInformation.objects.filter(
            employee_id__in=employees
        )
        employee_data = request.data.get("employee_data", {})
        work_info_data = request.data.get("employee_work_info", {})
        fields_to_remove = [
            "badge_id",
            "employee_first_name",
            "employee_last_name",
            "is_active",
            "email",
            "phone",
            "employee_bank_details__account_number",
        ]
        for field in fields_to_remove:
            employee_data.pop(field, None)
            work_info_data.pop(field, None)

        try:
            employees.update(**employee_data)
            employee_work_info.update(**work_info_data)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        return Response({"status": "success"}, status=200)


class ActiontypeView(APIView):
    serializer_class = ActiontypeSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            action_type = object_check(Actiontype, pk)
            if action_type is None:
                return Response({"error": "Actiontype not found"}, status=404)
            serializer = self.serializer_class(action_type)
            return Response(serializer.data, status=200)
        action_types = Actiontype.objects.all()
        paginater = PageNumberPagination()
        page = paginater.paginate_queryset(action_types, request)
        serializer = self.serializer_class(page, many=True)
        return paginater.get_paginated_response(serializer.data)

    def post(self, request):
        if permission_check(request, "employee.add_actiontype") is False:
            return Response({"error": "No permission"}, status=401)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        if permission_check(request, "employee.change_actiontype") is False:
            return Response({"error": "No permission"}, status=401)
        action_type = object_check(Actiontype, pk)
        if action_type is None:
            return Response({"error": "Actiontype not found"}, status=404)
        serializer = self.serializer_class(action_type, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        if permission_check(request, "employee.delete_actiontype") is False:
            return Response({"error": "No permission"}, status=401)
        action_type = object_check(Actiontype, pk)
        if action_type is None:
            return Response({"error": "Actiontype not found"}, status=404)
        response, status_code = object_delete(Actiontype, pk)
        return Response(response, status=status_code)


class DisciplinaryActionAPIView(APIView):
    """
    Endpoint for managing disciplinary actions.

    Permissions:
        - Requires authentication.

    Methods:
        get(request, pk=None):
            - Retrieves a specific disciplinary action by `pk` or lists all disciplinary actions with optional filtering.

        post(request):
            - Creates a new disciplinary action.

        put(request, pk):
            - Updates an existing disciplinary action by `pk`.

        delete(request, pk):
            - Deletes a specific disciplinary action by `pk`.
    """

    filterset_class = DisciplinaryActionFilter
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return DisciplinaryAction.objects.get(pk=pk)
        except DisciplinaryAction.DoesNotExist:
            raise Http404

    def get(self, request, pk=None):
        if pk:
            employee = request.user.employee_get
            disciplinary_action = self.get_object(pk)
            is_manager = (
                True
                if employee.get_subordinate_employees()
                & disciplinary_action.employee_id.all()
                else False
            )
            if (
                (employee == disciplinary_action.employee_id)
                or is_manager
                or request.user.has_perm("employee.view_disciplinaryaction")
            ):
                serializer = DisciplinaryActionSerializer(disciplinary_action)
                return Response(serializer.data, status=200)
            return Response({"error": "No permission"}, status=400)
        else:
            employee = request.user.employee_get
            is_manager = EmployeeWorkInformation.objects.filter(
                reporting_manager_id=employee
            ).exists()
            subordinates = employee.get_subordinate_employees()

            if request.user.has_perm("employee.view_disciplinaryaction"):
                queryset = DisciplinaryAction.objects.all()
            elif is_manager:
                queryset_subordinates = DisciplinaryAction.objects.filter(
                    employee_id__in=subordinates
                )
                queryset_employee = DisciplinaryAction.objects.filter(
                    employee_id=employee
                )
                queryset = queryset_subordinates | queryset_employee
            else:
                queryset = DisciplinaryAction.objects.filter(employee_id=employee)

            paginator = PageNumberPagination()
            disciplinary_actions = queryset
            disciplinary_action_filter_queryset = self.filterset_class(
                request.GET, queryset=disciplinary_actions
            ).qs
            page = paginator.paginate_queryset(
                disciplinary_action_filter_queryset, request
            )
            serializer = DisciplinaryActionSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        if permission_check(request, "employee.add_disciplinaryaction") is False:
            return Response({"error": "No permission"}, status=401)
        serializer = DisciplinaryActionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        if permission_check(request, "employee.add_disciplinaryaction") is False:
            return Response({"error": "No permission"}, status=401)
        disciplinary_action = self.get_object(pk)
        serializer = DisciplinaryActionSerializer(
            disciplinary_action, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if permission_check(request, "employee.add_disciplinaryaction") is False:
            return Response({"error": "No permission"}, status=401)
        disciplinary_action = self.get_object(pk)
        disciplinary_action.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PolicyAPIView(APIView):
    """
    Endpoint for managing policies.

    Permissions:
        - Requires authentication.

    Methods:
        get(request, pk=None):
            - Retrieves a specific policy by `pk` or lists all policies with optional search functionality.

        post(request):
            - Creates a new policy.

        put(request, pk):
            - Updates an existing policy by `pk`.

        delete(request, pk):
            - Deletes a specific policy by `pk`.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Policy.objects.get(pk=pk)
        except Policy.DoesNotExist:
            raise Http404

    def get(self, request, pk=None):
        if pk:
            policy = self.get_object(pk)
            serializer = PolicySerializer(policy)
            return Response(serializer.data)
        else:
            search = request.GET.get("search", None)
            if search:
                policies = Policy.objects.filter(title__icontains=search)
            else:
                policies = Policy.objects.all()
            serializer = PolicySerializer(policies, many=True)
            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(policies, request)
            serializer = PolicySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

    def _parse_multipart_policy_data(self, request):
        """Parse multipart form data for policy create/update (matches Django PolicyForm)."""
        data = request.data
        files = []
        if hasattr(request, 'FILES') and request.FILES:
            files = request.FILES.getlist('attachment') or []
        company_ids = data.getlist('company_id') if hasattr(data, 'getlist') else (data.get('company_id') or [])
        if not isinstance(company_ids, list):
            company_ids = [company_ids] if company_ids else []
        company_ids = [int(x) for x in company_ids if x is not None and str(x).strip() and str(x).replace('-', '').isdigit()]
        is_visible_val = data.get('is_visible_to_all', 'true')
        if isinstance(is_visible_val, bool):
            is_visible = is_visible_val
        else:
            is_visible = str(is_visible_val).lower() in ('true', '1', 'yes')
        return {
            'title': data.get('title', ''),
            'body': data.get('body', ''),
            'is_visible_to_all': is_visible,
            'company_id': company_ids,
            'attachment_files': list(files),
        }

    def post(self, request):
        if permission_check(request, "employee.add_policy") is False:
            return Response({"error": "No permission"}, status=401)

        content_type = getattr(request, 'content_type', '') or ''
        is_multipart = 'multipart/form-data' in content_type
        if is_multipart and request.FILES:
            parsed = self._parse_multipart_policy_data(request)
            serializer = PolicySerializer(data={
                'title': parsed['title'],
                'body': parsed['body'],
                'is_visible_to_all': parsed['is_visible_to_all'],
                'company_id': parsed['company_id'] or [],
            })
            if serializer.is_valid():
                policy = serializer.save()
                for f in parsed['attachment_files']:
                    pmf = PolicyMultipleFile(attachment=f)
                    pmf.save()
                    policy.attachments.add(pmf)
                return Response(PolicySerializer(policy).data, status=201)
            return Response(serializer.errors, status=400)

        serializer = PolicySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        if permission_check(request, "employee.change_policy") is False:
            return Response({"error": "No permission"}, status=401)
        policy = self.get_object(pk)

        content_type = getattr(request, 'content_type', '') or ''
        is_multipart = 'multipart/form-data' in content_type
        if is_multipart and (request.FILES or request.POST):
            parsed = self._parse_multipart_policy_data(request)
            serializer = PolicySerializer(policy, data={
                'title': parsed['title'],
                'body': parsed['body'],
                'is_visible_to_all': parsed['is_visible_to_all'],
                'company_id': parsed['company_id'] or [],
            }, partial=True)
            if serializer.is_valid():
                policy = serializer.save()
                for f in parsed['attachment_files']:
                    pmf = PolicyMultipleFile(attachment=f)
                    pmf.save()
                    policy.attachments.add(pmf)
                return Response(PolicySerializer(policy).data)
            return Response(serializer.errors, status=400)

        serializer = PolicySerializer(policy, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    # def delete(self, request, pk):
    #     if permission_check(request, "employee.delete_policy") is False:
    #         return Response({"error": "No permission"}, status=401)
    #     policy = self.get_object(pk)
    #     policy.delete()
    #     return Response({"message": "Policy deleted"}, status=200)

    # def delete(self, request, pk):
    #    if permission_check(request, "employee.delete_policy") is False:
    #     return Response({"error": "No permission"}, status=401)
    #    try:
    #        policy = self.get_object(pk)
    #        policy.delete()
    #        return Response({"message": "Policy deleted"}, status=200)
    #    except Http404:
    #         return Response({"error": "Policy not found"}, status=404)


    def delete(self, request, pk):
      if permission_check(request, "employee.delete_policy") is False:
        return Response({"error": "No permission"}, status=401)
      try:
        policy = self.get_object(pk)
        # Clear M2M relationships BEFORE deletion to avoid errors
        policy.attachments.clear()
        policy.specific_employees.clear()
        policy.company_id.clear()
        # Delete the policy
        policy.delete()
        return Response({"message": "Policy deleted successfully"}, status=200)
      except Http404:
        return Response({"error": "Policy not found"}, status=404)
      except Exception as e:
        # Check if policy was actually deleted despite the error
        try:
            Policy.objects.get(pk=pk)
            # Policy still exists, return error
            return Response({"error": str(e)}, status=500)
        except Policy.DoesNotExist:
            # Policy was deleted successfully, return success even if cleanup had issues
            return Response({"message": "Policy deleted successfully"}, status=200)
        
class DocumentRequestAPIView(APIView):
    """
    Endpoint for managing document requests.

    Permissions:
        - Requires authentication.
        - Specific actions require manager-level permissions.

    Methods:
        get(request, pk=None):
            - Retrieves a specific document request by `pk` or lists all document requests with pagination.

        post(request):
            - Creates a new document request and notifies relevant employees.

        put(request, pk):
            - Updates an existing document request by `pk`.

        delete(request, pk):
            - Deletes a specific document request by `pk`.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return DocumentRequest.objects.get(pk=pk)
        except DocumentRequest.DoesNotExist:
            raise Http404

    def get(self, request, pk=None):
        if pk:
            document_request = self.get_object(pk)
            serializer = DocumentRequestSerializer(document_request)
            return Response(serializer.data)
        else:
            document_requests = DocumentRequest.objects.all()
            pagination = PageNumberPagination()
            page = pagination.paginate_queryset(document_requests, request)
            serializer = DocumentRequestSerializer(page, many=True)
            return pagination.get_paginated_response(serializer.data)

    @manager_permission_required("horilla_documents.add_documentrequests")
    def post(self, request):
        serializer = DocumentRequestSerializer(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            try:
                employees = [user.employee_user_id for user in obj.employee_id.all()]

                notify.send(
                    request.user.employee_get,
                    recipient=employees,
                    verb=f"{request.user.employee_get} requested a document.",
                    verb_ar=f"طلب {request.user.employee_get} مستنداً.",
                    verb_de=f"{request.user.employee_get} hat ein Dokument angefordert.",
                    verb_es=f"{request.user.employee_get} solicitó un documento.",
                    verb_fr=f"{request.user.employee_get} a demandé un document.",
                    redirect="/employee/employee-profile",
                    icon="chatbox-ellipses",
                    api_redirect=f"/api/employee/document-request/{obj.id}",
                )
            except:
                pass
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @manager_permission_required("horilla_documents.change_documentrequests")
    def put(self, request, pk):
        document_request = self.get_object(pk)
        serializer = DocumentRequestSerializer(document_request, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_decorator(permission_required("employee.delete_employee"))
    def delete(self, request, pk):
        try:
            document_request = self.get_object(pk)
            
            # Check for related documents before deletion
            related_documents = Document.objects.filter(document_request_id=document_request)
            if related_documents.exists():
                return Response(
                    {
                        "error": "Cannot delete document request. Related documents found.",
                        "related_documents": [
                            {
                                "id": doc.id,
                                "title": doc.title,
                                "status": doc.status
                            }
                            for doc in related_documents
                        ],
                        "count": related_documents.count(),
                        "message": "Please delete the related documents first, then try again.",
                        "action_required": "Delete related documents using: DELETE /api/v1/employee/documents/<document_id>/"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Clear M2M relationships BEFORE deletion to avoid errors
            document_request.employee_id.clear()
            # Delete the document request
            document_request.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Http404:
            return Response({"error": "Document request not found"}, status=status.HTTP_404_NOT_FOUND)
        except ProtectedError as e:
            # Fallback: Handle protected error if check above didn't catch it
            try:
                document_request = self.get_object(pk)
                related_documents = Document.objects.filter(document_request_id=document_request)
                return Response(
                    {
                        "error": "Cannot delete document request due to protected relationships.",
                        "related_documents": [
                            {
                                "id": doc.id,
                                "title": doc.title,
                                "status": doc.status
                            }
                            for doc in related_documents
                        ],
                        "count": related_documents.count(),
                        "message": "Please delete the related documents first, then try again.",
                        "action_required": "Delete related documents using: DELETE /api/v1/employee/documents/<document_id>/"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Http404:
                return Response({"error": "Document request not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentAPIView(APIView):
    filterset_class = DocumentRequestFilter
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            raise Http404

    def get(self, request, pk=None):
        if pk:
            document = self.get_object(pk)
            serializer = DocumentSerializer(document)
            return Response(serializer.data)
        else:
            documents = Document.objects.all()
            document_requests_filtered = self.filterset_class(
                request.GET, queryset=documents
            ).qs
            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(document_requests_filtered, request)
            serializer = DocumentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

    @manager_or_owner_permission_required(
        DocumentRequest, "horilla_documents.add_document"
    )
    def post(self, request):
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            try:
                notify.send(
                    request.user.employee_get,
                    recipient=request.user.employee_get.get_reporting_manager().employee_user_id,
                    verb=f"{request.user.employee_get} uploaded a document",
                    verb_ar=f"قام {request.user.employee_get} بتحميل مستند",
                    verb_de=f"{request.user.employee_get} hat ein Dokument hochgeladen",
                    verb_es=f"{request.user.employee_get} subió un documento",
                    verb_fr=f"{request.user.employee_get} a téléchargé un document",
                    redirect=f"/employee/employee-view/{request.user.employee_get.id}/",
                    icon="chatbox-ellipses",
                    api_redirect=f"/api/employee/documents/",
                )
            except:
                pass
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_decorator(owner_can_enter("horilla_documents.change_document", Employee))
    def put(self, request, pk):
        document = self.get_object(pk)
        serializer = DocumentSerializer(document, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_decorator(owner_can_enter("horilla_documents.delete_document", Employee))
    def delete(self, request, pk):
        document = self.get_object(pk)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentViewAPIView(APIView):
    """
    Endpoint for viewing/downloading document files.
    Serves the document file with proper authentication and permissions.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        Serve the document file for viewing/downloading.
        """
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if document has a file
        if not document.document:
            return Response(
                {"error": "Document file not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions - user must be able to view the document
        # Allow if user is the document owner, manager, or has view permission
        try:
            # Check if user has permission to view document requests
            if not request.user.has_perm("horilla_documents.view_documentrequest"):
                # Check if user is the document owner
                if hasattr(request.user, "employee_get"):
                    employee = request.user.employee_get
                    if document.employee_id != employee:
                        return Response(
                            {"error": "Permission denied"},
                            status=status.HTTP_403_FORBIDDEN,
                        )
                else:
                    return Response(
                        {"error": "Permission denied"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
        except Exception:
            # If permission check fails, allow if user is authenticated
            pass

        # Serve the file
        try:
            # Use Django's file storage abstraction - works with both local and remote storage
            file_field = document.document
            
            # Validate file field has a name
            if not file_field.name:
                return Response(
                    {"error": "Document file name is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Get file name for content type detection and filename
            file_name = file_field.name
            
            # Determine content type based on file extension
            content_type, _ = mimetypes.guess_type(file_name)
            if not content_type:
                content_type = "application/octet-stream"
            
            # Open file using Django's storage abstraction
            # This works with both local filesystem and remote storage (S3, etc.)
            try:
                file_handle = file_field.open('rb')
            except Exception as open_error:
                logger.error(f"Error opening document file: {open_error}", exc_info=True)
                return Response(
                    {"error": f"Failed to open document file: {str(open_error)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            
            # Create FileResponse
            # FileResponse will automatically close the file handle when done
            file_response = FileResponse(file_handle, content_type=content_type)
            filename = file_name.split("/")[-1] if "/" in file_name else file_name
            file_response[
                "Content-Disposition"
            ] = f'inline; filename="{filename}"'
            
            # Set content length if available
            try:
                if hasattr(file_field, 'size') and file_field.size:
                    file_response["Content-Length"] = str(file_field.size)
            except (AttributeError, NotImplementedError):
                pass
            
            return file_response
        except FileNotFoundError:
            return Response(
                {"error": "Document file not found on server"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error serving document file: {e}", exc_info=True)
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {"error": f"Failed to serve document file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DocumentRequestApproveRejectView(APIView):
    permission_classes = [IsAuthenticated]

    @manager_permission_required("horilla_documents.add_document")
    def post(self, request, id, status):
        document = Document.objects.filter(id=id).first()
        document.status = status
        document.save()
        return Response({"status": "success"}, status=200)


class DocumentBulkApproveRejectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @manager_permission_required("horilla_documents.add_document")
    def put(self, request):
        ids = request.data.get("ids", None)
        status = request.data.get("status", None)
        status_code = 200
        response = []

        if ids:
            documents = Document.objects.filter(id__in=ids)
            for document in documents:
                if not document.document:
                    status_code = 400
                    response.append({"id": document.id, "error": "No documents"})
                    continue
                response.append({"id": document.id, "status": "success"})
                document.status = status
                document.save()
        else:
            status_code = 400
            response.append({"error": "No ids provided"})
        return Response(response, status=status_code)
    
    @manager_permission_required("horilla_documents.add_document")
    def post(self, request, id, status):
      document = Document.objects.filter(id=id).first()
      if not document:
        return Response({"error": "Document not found"}, status=404)
      document.status = status
      document.save()
      return Response({"status": "success"}, status=200)

class OrganizationChartAPIView(APIView):
    """
    API endpoint for organization chart.
    Returns the hierarchy structure matching the backend Django view logic exactly.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get organization chart data.
        Query params:
        - manager_id: Optional manager ID to view chart from (defaults to current user's employee)
        - employee_work_info__company_id: Optional company filter
        """
        from django.db.models import Exists, OuterRef

        # Get company filter from query params or session
        company_id = request.GET.get("employee_work_info__company_id")
        if not company_id:
            # Try to get from session/context if available
            company_id = getattr(request, "selected_company", None)
            if company_id == "all":
                company_id = None

        # Find employees who ARE reporting managers (have subordinates)
        if company_id:
            reporting_managers = Employee.objects.filter(
                is_active=True,
                employee_work_info__company_id=company_id,
            ).annotate(
                has_subordinates=Exists(
                    EmployeeWorkInformation.objects.filter(
                        reporting_manager_id=OuterRef("pk")
                    )
                )
            ).filter(has_subordinates=True).distinct()
        else:
            reporting_managers = Employee.objects.filter(
                is_active=True,
            ).annotate(
                has_subordinates=Exists(
                    EmployeeWorkInformation.objects.filter(
                        reporting_manager_id=OuterRef("pk")
                    )
                )
            ).filter(has_subordinates=True).distinct()

        # Create dictionary of reporting manager id -> name
        result_dict = {item.id: item.get_full_name() for item in reporting_managers}

        entered_req_managers = []

        # Helper function to recursively create the hierarchy structure (matches backend exactly)
        def create_hierarchy(manager):
            """
            Hierarchy generator method - matches backend logic exactly
            """
            """
            Hierarchy generator method - matches backend logic exactly
            """
            nodes = []
            # Check if manager is a reporting manager, if yes store it
            if manager.id in result_dict.keys():
                entered_req_managers.append(manager)

            # Filter subordinates
            subordinates = Employee.objects.filter(
                is_active=True, employee_work_info__reporting_manager_id=manager
            ).exclude(id=manager.id)

            # Iterate through subordinates
            for employee in subordinates:
                if employee in entered_req_managers:
                    continue

                # Check if employee is a reporting manager
                if employee.id in result_dict.keys():
                    nodes.append(
                        {
                            "name": employee.get_full_name(),
                            "title": getattr(
                                employee.get_job_position(),
                                "job_position",
                                "Not set",
                            ),
                            "children": create_hierarchy(employee),
                        }
                    )
                    entered_req_managers.append(employee)
                else:
                    nodes.append(
                        {
                            "name": employee.get_full_name(),
                            "title": getattr(
                                employee.get_job_position(),
                                "job_position",
                                "Not set",
                            ),
                            "className": "middle-level",
                            "children": create_hierarchy(employee),
                        }
                    )
            return nodes

        # Get manager to display chart from
        manager_id = request.GET.get("manager_id")
        if manager_id:
            try:
                manager = Employee.objects.get(id=int(manager_id))
            except (Employee.DoesNotExist, ValueError):
                return Response(
                    {"error": "Manager not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Default to current user's employee
            if hasattr(request.user, "employee_get"):
                manager = request.user.employee_get
            else:
                return Response(
                    {"error": "User has no associated employee"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Build reporting manager dropdown options
        if len(reporting_managers) == 0:
            reporting_manager_dict = {}
        else:
            # Backend adds "My view" for first manager
            first_manager_id = reporting_managers[0].id
            reporting_manager_dict = {
                first_manager_id: "My view",
                **{item.id: item.get_full_name() for item in reporting_managers},
            }

        # Build the root node
        node = {
            "name": manager.get_full_name(),
            "title": getattr(manager.get_job_position(), "job_position", "Not set"),
            "children": create_hierarchy(manager),
        }

        return Response(
            {
                "act_datasource": node,
                "reporting_manager_dict": reporting_manager_dict,
                "act_manager_id": manager.id,
            },
            status=status.HTTP_200_OK,
        )


class EmployeeBulkArchiveView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("employee.delete_employee"))
    def post(self, request, is_active):
        # Convert string parameter to boolean
        if isinstance(is_active, str):
            is_active = is_active.lower() == 'true'
        
        ids = request.data.get("ids")
        
        # Validate that ids is provided and is a list
        if not ids:
            return Response(
                {"error": "Please provide 'ids' field with a list of employee IDs"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(ids, list):
            return Response(
                {"error": "'ids' must be a list of employee IDs"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(ids) == 0:
            return Response(
                {"error": "Please provide at least one employee ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        errors = []
        
        for employee_id in ids:
            try:
                employee = Employee.objects.get(id=employee_id)
                employee.is_active = is_active
                employee.employee_user_id.is_active = is_active
                
                # Check if employee can be archived
                archive_condition = employee.get_archive_condition()
                if archive_condition is False:
                    employee.save()
                    results.append({
                        "employee_id": employee_id,
                        "employee": str(employee),
                        "status": "archived" if not is_active else "unarchived",
                        "success": True
                    })
                else:
                    # Employee cannot be archived due to related models
                    errors.append({
                        "employee_id": employee_id,
                        "employee": str(employee),
                        "error": archive_condition if isinstance(archive_condition, dict) else "Related model found for this employee",
                        "success": False
                    })
            except Employee.DoesNotExist:
                errors.append({
                    "employee_id": employee_id,
                    "error": "Employee not found",
                    "success": False
                })
            except Exception as e:
                errors.append({
                    "employee_id": employee_id,
                    "error": str(e),
                    "success": False
                })
        
        return Response({
            "success": len(errors) == 0,
            "results": results,
            "errors": errors,
            "total": len(ids),
            "successful": len(results),
            "failed": len(errors)
        }, status=200)


class EmployeeArchiveView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("employee.delete_employee"))
    def post(self, request, id, is_active):
        # Convert string parameter to boolean
        if isinstance(is_active, str):
            is_active = is_active.lower() == 'true'
        
        employee = Employee.objects.get(id=id)
        employee.is_active = is_active
        employee.employee_user_id.is_active = is_active
        response = None
        if employee.get_archive_condition() is False:
            employee.save()
        else:
            response = {
                "employee": str(employee),
                "error": employee.get_archive_condition(),
            }
        return Response(response, status=200)


class EmployeeBulkMailView(APIView):
    """
    Send bulk mail to selected employees (matches backend send_mail_to_employee).
    POST body: { "subject": str, "body": str (HTML), "employee_ids": [id, ...] }
    """

    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("employee.change_employee"), name="dispatch")
    def post(self, request):
        subject = request.data.get("subject", "").strip()
        body = request.data.get("body", "").strip()
        employee_ids = request.data.get("employee_ids") or []

        if not subject:
            return Response(
                {"error": "Subject is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not body:
            return Response(
                {"error": "Message body is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not employee_ids or not isinstance(employee_ids, list):
            return Response(
                {"error": "employee_ids must be a non-empty list of employee IDs"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = []
        errors = []
        sender_employee = getattr(request.user, "employee_get", None)

        for emp_id in employee_ids:
            try:
                employee = Employee.objects.get(id=emp_id)
            except Employee.DoesNotExist:
                errors.append({"employee_id": emp_id, "error": "Employee not found"})
                continue

            send_to_mail = None
            if getattr(employee, "employee_work_info", None) and getattr(
                employee.employee_work_info, "email", None
            ):
                send_to_mail = employee.employee_work_info.email
            if not send_to_mail:
                send_to_mail = getattr(employee, "email", None)
            if not send_to_mail:
                errors.append(
                    {
                        "employee_id": emp_id,
                        "employee": str(employee),
                        "error": "No email set for this employee",
                    }
                )
                continue

            try:
                template_bdy = Template(body)
                context = Context(
                    {
                        "instance": employee,
                        "self": sender_employee,
                        "request": request,
                    }
                )
                render_bdy = template_bdy.render(context)
            except Exception as e:
                errors.append(
                    {
                        "employee_id": emp_id,
                        "employee": str(employee),
                        "error": str(e),
                    }
                )
                continue

            try:
                email = EmailMessage(
                    subject=subject,
                    body=render_bdy,
                    to=[send_to_mail],
                )
                email.content_subtype = "html"
                email.send()
                results.append(
                    {
                        "employee_id": emp_id,
                        "employee": str(employee),
                        "email": send_to_mail,
                        "sent": True,
                    }
                )
            except Exception as e:
                errors.append(
                    {
                        "employee_id": emp_id,
                        "employee": str(employee),
                        "error": str(e),
                    }
                )

        return Response(
            {
                "success": len(errors) == 0,
                "sent": len(results),
                "failed": len(errors),
                "results": results,
                "errors": errors,
                "total": len(employee_ids),
            },
            status=200,
        )


class EmployeeSelectorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        employee = user.employee_get
        
        # Determine user's role
        user_role = self.get_user_role(user, employee)
        
        # Get employees based on role
        employees = self.get_employees_by_role(user, employee, user_role)
        
        # Apply additional filters
        employees = self.apply_filters(request, employees)
        
        # Add role information to response
        response_data = {
            "user_role": user_role,
            "total_employees": employees.count(),
            "role_description": self.get_role_description(user_role)
        }
        
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(employees, request)
        serializer = EmployeeSelectorSerializer(page, many=True)
        
        # Combine pagination data with role information
        paginated_response = paginator.get_paginated_response(serializer.data)
        paginated_response.data.update(response_data)
        
        return paginated_response
    
    def get_user_role(self, user, employee):
        """
        Determine user's role based on permissions and relationships
        """
        if not employee:
            return "GUEST"
        
        # Check if superuser
        if user.is_superuser:
            return "SUPERUSER"
        
        # Check if user has view all employees permission (CEO/Admin level)
        if user.has_perm("employee.view_all_employees") or user.has_perm("employee.view_employee"):
            # Check if has company-level access
            if hasattr(employee, 'employee_work_info') and employee.employee_work_info:
                return "CEO"
            return "ADMIN"
        
        # Check if user is a manager (has subordinates)
        is_manager = EmployeeWorkInformation.objects.filter(
            reporting_manager_id=employee
        ).exists()
        
        if is_manager:
            # Check if department manager
            if hasattr(employee, 'employee_work_info') and employee.employee_work_info:
                dept = employee.employee_work_info.department_id
                if dept:
                    # Check if manages entire department
                    dept_employees = EmployeeWorkInformation.objects.filter(
                        department_id=dept
                    ).exclude(reporting_manager_id=employee)
                    if not dept_employees.exists():
                        return "DEPARTMENT_MANAGER"
            return "TEAM_MANAGER"
        
        return "EMPLOYEE"
    
    def get_employees_by_role(self, user, employee, role):
        """
        Get employees based on user's role
        """
        if role == "SUPERUSER" or role == "ADMIN" or role == "CEO":
            # Superuser/Admin/CEO can see all employees
            return Employee.objects.filter(is_active=True)
        elif role == "DEPARTMENT_MANAGER":
            # Department manager sees employees in their department
            if hasattr(employee, 'employee_work_info') and employee.employee_work_info:
                dept = employee.employee_work_info.department_id
                if dept:
                    return Employee.objects.filter(
                        employee_work_info__department_id=dept,
                        is_active=True
                    )
        elif role == "TEAM_MANAGER":
            # Team manager sees their subordinates
            subordinates = employee.get_subordinate_employees() if hasattr(employee, 'get_subordinate_employees') else Employee.objects.none()
            # Include self
            return Employee.objects.filter(
                Q(id__in=subordinates.values_list('id', flat=True)) | Q(id=employee.id),
                is_active=True
            )
        else:
            # Regular employee sees only themselves
            return Employee.objects.filter(id=employee.id, is_active=True)
    
    def get_role_description(self, role):
        """
        Get description for user role
        """
        descriptions = {
            "SUPERUSER": "Superuser - Can view and manage all employees",
            "ADMIN": "Admin - Can view and manage all employees",
            "CEO": "CEO - Can view all employees in the company",
            "DEPARTMENT_MANAGER": "Department Manager - Can view employees in their department",
            "TEAM_MANAGER": "Team Manager - Can view and manage subordinates",
            "EMPLOYEE": "Employee - Can view only their own information",
            "GUEST": "Guest - Limited access"
        }
        return descriptions.get(role, "Unknown role")

    def apply_filters(self, request, employees):
        """
        Apply various filters to the employee queryset
        """
        # Search filter
        search = request.GET.get('search')
        if search:
            employees = employees.filter(
                Q(employee_first_name__icontains=search) |
                Q(employee_last_name__icontains=search) |
                Q(badge_id__icontains=search) |
                Q(email__icontains=search)
            )

        # Status filter
        is_active = request.GET.get('is_active')
        if is_active is not None:
            if is_active.lower() == 'true':
                employees = employees.filter(is_active=True)
            elif is_active.lower() == 'false':
                employees = employees.filter(is_active=False)

        # Department filter
        department_id = request.GET.get('department_id')
        if department_id:
            employees = employees.filter(employee_work_info__department_id=department_id)

        # Job position filter
        job_position_id = request.GET.get('job_position_id')
        if job_position_id:
            employees = employees.filter(employee_work_info__job_position_id=job_position_id)

        # Company filter (for CEO and superusers)
        company_id = request.GET.get('company_id')
        if company_id:
            employees = employees.filter(employee_work_info__company_id=company_id)

        return employees


class ReportingManagerCheck(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if Employee.objects.filter(
            employee_work_info__reporting_manager_id=request.user.employee_get
        ):
            return Response(status=200)
        return Response(status=404)

class EmployeeDashboardAPIView(APIView):
    """
    Role-based employee dashboard endpoint
    Provides different data based on user's role
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        employee = user.employee_get
        
        # Get user's role and employees
        user_role = self.get_user_role(user, employee)
        employees = self.get_employees_by_role(user, employee, user_role)
        
        # Get dashboard data based on role
        dashboard_data = self.get_dashboard_data(user, employee, user_role, employees)
        
        return Response(dashboard_data, status=200)
    
    def get_user_role(self, user, employee):
        """
        Determine user's role based on permissions and relationships
        """
        if not employee:
            return "GUEST"
        
        # Check if superuser
        if user.is_superuser:
            return "SUPERUSER"
        
        # Check if user has view all employees permission (CEO/Admin level)
        if user.has_perm("employee.view_all_employees") or user.has_perm("employee.view_employee"):
            # Check if has company-level access
            if hasattr(employee, 'employee_work_info') and employee.employee_work_info:
                return "CEO"
            return "ADMIN"
        
        # Check if user is a manager (has subordinates)
        is_manager = EmployeeWorkInformation.objects.filter(
            reporting_manager_id=employee
        ).exists()
        
        if is_manager:
            # Check if department manager
            if hasattr(employee, 'employee_work_info') and employee.employee_work_info:
                dept = employee.employee_work_info.department_id
                if dept:
                    # Check if manages entire department
                    dept_employees = EmployeeWorkInformation.objects.filter(
                        department_id=dept
                    ).exclude(reporting_manager_id=employee)
                    if not dept_employees.exists():
                        return "DEPARTMENT_MANAGER"
            return "TEAM_MANAGER"
        
        return "EMPLOYEE"
    
    def get_employees_by_role(self, user, employee, role):
        """
        Get employees based on user's role
        """
        if role == "SUPERUSER" or role == "ADMIN" or role == "CEO":
            # Superuser/Admin/CEO can see all employees
            return Employee.objects.filter(is_active=True)
        elif role == "DEPARTMENT_MANAGER":
            # Department manager sees employees in their department
            if hasattr(employee, 'employee_work_info') and employee.employee_work_info:
                dept = employee.employee_work_info.department_id
                if dept:
                    return Employee.objects.filter(
                        employee_work_info__department_id=dept,
                        is_active=True
                    )
        elif role == "TEAM_MANAGER":
            # Team manager sees their subordinates
            subordinates = employee.get_subordinate_employees() if hasattr(employee, 'get_subordinate_employees') else Employee.objects.none()
            # Include self
            return Employee.objects.filter(
                Q(id__in=subordinates.values_list('id', flat=True)) | Q(id=employee.id),
                is_active=True
            )
        else:
            # Regular employee sees only themselves
            return Employee.objects.filter(id=employee.id, is_active=True)

    def get_dashboard_data(self, user, employee, role, employees):
        """
        Get dashboard data based on user's role
        """
        if role == "SUPERUSER":
            return self.get_superuser_dashboard(employees)
        elif role == "CEO":
            return self.get_ceo_dashboard(employees)
        elif role == "DEPARTMENT_MANAGER":
            return self.get_department_manager_dashboard(employees, employee)
        elif role == "TEAM_MANAGER":
            return self.get_team_manager_dashboard(employees, employee)
        else:
            return self.get_regular_employee_dashboard(employee)

    def get_superuser_dashboard(self, employees):
        """
        Superuser dashboard with system-wide statistics
        """
        from base.models import Company, Department
        
        companies = Company.objects.all()
        departments = Department.objects.all()
        
        return {
            "role": "SUPERUSER",
            "total_employees": employees.count(),
            "active_employees": employees.filter(is_active=True).count(),
            "inactive_employees": employees.filter(is_active=False).count(),
            "companies_count": companies.count(),
            "departments_count": departments.count(),
            "system_stats": {
                "total_users": employees.count(),
                "total_companies": companies.count(),
                "total_departments": departments.count()
            }
        }

    def get_ceo_dashboard(self, employees):
        """
        CEO dashboard with company-wide statistics
        """
        from base.models import Department, JobPosition
        
        company = employees.first().get_company() if employees.exists() else None
        
        if company:
            departments = Department.objects.filter(company_id=company)
            job_positions = JobPosition.objects.filter(company_id=company)
            
            # Department-wise employee count
            dept_stats = []
            for dept in departments:
                dept_employee_count = employees.filter(
                    employee_work_info__department_id=dept
                ).count()
                dept_stats.append({
                    "department": dept.department,
                    "employee_count": dept_employee_count
                })
            
            return {
                "role": "CEO",
                "company": company.company,
                "total_employees": employees.count(),
                "active_employees": employees.filter(is_active=True).count(),
                "departments_count": departments.count(),
                "job_positions_count": job_positions.count(),
                "department_statistics": dept_stats,
                "company_stats": {
                    "total_employees": employees.count(),
                    "total_departments": departments.count(),
                    "total_positions": job_positions.count()
                }
            }
        
        return {
            "role": "CEO",
            "message": "No company assigned",
            "total_employees": 0
        }

    def get_department_manager_dashboard(self, employees, manager):
        """
        Department manager dashboard with department statistics
        """
        work_info = manager.employee_work_info
        department = work_info.department_id if work_info else None
        
        if department:
            # Get job positions in the department
            job_positions = JobPosition.objects.filter(department_id=department)
            
            # Position-wise employee count
            position_stats = []
            for position in job_positions:
                position_employee_count = employees.filter(
                    employee_work_info__job_position_id=position
                ).count()
                position_stats.append({
                    "position": position.job_position,
                    "employee_count": position_employee_count
                })
            
            return {
                "role": "DEPARTMENT_MANAGER",
                "department": department.department,
                "total_employees": employees.count(),
                "active_employees": employees.filter(is_active=True).count(),
                "job_positions_count": job_positions.count(),
                "position_statistics": position_stats,
                "department_stats": {
                    "total_employees": employees.count(),
                    "total_positions": job_positions.count(),
                    "manager_name": manager.get_full_name()
                }
            }
        
        return {
            "role": "DEPARTMENT_MANAGER",
            "message": "No department assigned",
            "total_employees": 0
        }

    def get_team_manager_dashboard(self, employees, manager):
        """
        Team manager dashboard with team statistics
        """
        # Get direct subordinates
        direct_subordinates = employees.filter(
            employee_work_info__reporting_manager_id=manager
        ).exclude(pk=manager.pk)
        
        # Get subordinates by department
        dept_stats = {}
        for emp in direct_subordinates:
            dept = emp.get_department()
            if dept:
                dept_name = dept.department
                if dept_name not in dept_stats:
                    dept_stats[dept_name] = 0
                dept_stats[dept_name] += 1
        
        return {
            "role": "TEAM_MANAGER",
            "total_team_members": direct_subordinates.count(),
            "active_team_members": direct_subordinates.filter(is_active=True).count(),
            "department_distribution": dept_stats,
            "team_stats": {
                "total_members": direct_subordinates.count(),
                "active_members": direct_subordinates.filter(is_active=True).count(),
                "manager_name": manager.get_full_name()
            }
        }

    def get_regular_employee_dashboard(self, employee):
        """
        Regular employee dashboard with personal information
        """
        work_info = employee.employee_work_info
        
        return {
            "role": "REGULAR_EMPLOYEE",
            "employee_name": employee.get_full_name(),
            "badge_id": employee.badge_id,
            "email": employee.email,
            "department": work_info.department_id.department if work_info and work_info.department_id else None,
            "job_position": work_info.job_position_id.job_position if work_info and work_info.job_position_id else None,
            "reporting_manager": work_info.reporting_manager_id.get_full_name() if work_info and work_info.reporting_manager_id else None,
            "personal_stats": {
                "name": employee.get_full_name(),
                "status": "Active" if employee.is_active else "Inactive",
                "joining_date": work_info.date_joining if work_info else None
            }
        }

class RoleBasedEmployeeListAPIView(APIView):
    """
    Role-based employee listing with different data based on user role
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        employee = user.employee_get
        
        # Get user's role and employees
        user_role = self.get_user_role(user, employee)
        employees = self.get_employees_by_role(user, employee, user_role)
        
        # Apply filters
        employees = self.apply_filters(request, employees)
        
        # Get additional data based on role
        additional_data = self.get_role_specific_data(user_role, employees, employee)
        
        # Paginate results
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(employees, request)
        serializer = EmployeeListSerializer(page, many=True)
        
        # Combine pagination with role-specific data
        response_data = paginator.get_paginated_response(serializer.data)
        response_data.data.update(additional_data)
        
        return response_data
    
    def get_user_role(self, user, employee):
        """
        Determine user's role based on permissions and relationships
        """
        if not employee:
            return "GUEST"
        
        # Check if superuser
        if user.is_superuser:
            return "SUPERUSER"
        
        # Check if user has view all employees permission (CEO/Admin level)
        if user.has_perm("employee.view_all_employees") or user.has_perm("employee.view_employee"):
            # Check if has company-level access
            if hasattr(employee, 'employee_work_info') and employee.employee_work_info:
                return "CEO"
            return "ADMIN"
        
        # Check if user is a manager (has subordinates)
        is_manager = EmployeeWorkInformation.objects.filter(
            reporting_manager_id=employee
        ).exists()
        
        if is_manager:
            # Check if department manager
            if hasattr(employee, 'employee_work_info') and employee.employee_work_info:
                dept = employee.employee_work_info.department_id
                if dept:
                    # Check if manages entire department
                    dept_employees = EmployeeWorkInformation.objects.filter(
                        department_id=dept
                    ).exclude(reporting_manager_id=employee)
                    if not dept_employees.exists():
                        return "DEPARTMENT_MANAGER"
            return "TEAM_MANAGER"
        
        return "EMPLOYEE"
    
    def get_employees_by_role(self, user, employee, role):
        """
        Get employees based on user's role
        """
        if role == "SUPERUSER" or role == "ADMIN" or role == "CEO":
            # Superuser/Admin/CEO can see all employees
            return Employee.objects.filter(is_active=True)
        elif role == "DEPARTMENT_MANAGER":
            # Department manager sees employees in their department
            if hasattr(employee, 'employee_work_info') and employee.employee_work_info:
                dept = employee.employee_work_info.department_id
                if dept:
                    return Employee.objects.filter(
                        employee_work_info__department_id=dept,
                        is_active=True
                    )
        elif role == "TEAM_MANAGER":
            # Team manager sees their subordinates
            subordinates = employee.get_subordinate_employees() if hasattr(employee, 'get_subordinate_employees') else Employee.objects.none()
            # Include self
            return Employee.objects.filter(
                Q(id__in=subordinates.values_list('id', flat=True)) | Q(id=employee.id),
                is_active=True
            )
        else:
            # Regular employee sees only themselves
            return Employee.objects.filter(id=employee.id, is_active=True)

    def apply_filters(self, request, employees):
        """
        Apply filters to employee queryset
        """
        # Search filter
        search = request.GET.get('search')
        if search:
            employees = employees.filter(
                Q(employee_first_name__icontains=search) |
                Q(employee_last_name__icontains=search) |
                Q(badge_id__icontains=search)
            )

        # Department filter
        department_id = request.GET.get('department_id')
        if department_id:
            employees = employees.filter(employee_work_info__department_id=department_id)

        # Job position filter
        job_position_id = request.GET.get('job_position_id')
        if job_position_id:
            employees = employees.filter(employee_work_info__job_position_id=job_position_id)

        # Status filter
        is_active = request.GET.get('is_active')
        if is_active is not None:
            if is_active.lower() == 'true':
                employees = employees.filter(is_active=True)
            elif is_active.lower() == 'false':
                employees = employees.filter(is_active=False)

        return employees

    def get_role_specific_data(self, role, employees, employee):
        """
        Get role-specific additional data
        """
        if role == "CEO":
            return self.get_ceo_specific_data(employees)
        elif role == "DEPARTMENT_MANAGER":
            return self.get_department_manager_specific_data(employees, employee)
        elif role == "TEAM_MANAGER":
            return self.get_team_manager_specific_data(employees, employee)
        else:
            return {"role": role}

    def get_ceo_specific_data(self, employees):
        """
        CEO-specific data including company overview
        """
        from base.models import Company, Department
        
        company = employees.first().get_company() if employees.exists() else None
        
        if company:
            departments = Department.objects.filter(company_id=company)
            
            dept_summary = []
            for dept in departments:
                dept_employee_count = employees.filter(
                    employee_work_info__department_id=dept
                ).count()
                dept_summary.append({
                    "department_id": dept.id,
                    "department_name": dept.department,
                    "employee_count": dept_employee_count
                })
            
            return {
                "role": "CEO",
                "company": company.company,
                "department_summary": dept_summary,
                "total_employees": employees.count()
            }
        
        return {"role": "CEO", "message": "No company data available"}

    def get_department_manager_specific_data(self, employees, manager):
        """
        Department manager-specific data
        """
        work_info = manager.employee_work_info
        department = work_info.department_id if work_info else None
        
        if department:
            # Get job positions in the department
            job_positions = JobPosition.objects.filter(department_id=department)
            
            position_summary = []
            for position in job_positions:
                position_employee_count = employees.filter(
                    employee_work_info__job_position_id=position
                ).count()
                position_summary.append({
                    "position_id": position.id,
                    "position_name": position.job_position,
                    "employee_count": position_employee_count
                })
            
            return {
                "role": "DEPARTMENT_MANAGER",
                "department": department.department,
                "position_summary": position_summary,
                "total_employees": employees.count()
            }
        
        return {"role": "DEPARTMENT_MANAGER", "message": "No department data available"}

    def get_team_manager_specific_data(self, employees, manager):
        """
        Team manager-specific data
        """
        # Get direct subordinates
        direct_subordinates = employees.filter(
            employee_work_info__reporting_manager_id=manager
        ).exclude(pk=manager.pk)
        
        # Group by department
        dept_groups = {}
        for emp in direct_subordinates:
            dept = emp.get_department()
            if dept:
                dept_name = dept.department
                if dept_name not in dept_groups:
                    dept_groups[dept_name] = []
                dept_groups[dept_name].append({
                    "id": emp.id,
                    "name": emp.get_full_name(),
                    "position": emp.get_job_position().job_position if emp.get_job_position() else None
                })
        
        return {
            "role": "TEAM_MANAGER",
            "team_summary": dept_groups,
            "total_team_members": direct_subordinates.count()
        }
