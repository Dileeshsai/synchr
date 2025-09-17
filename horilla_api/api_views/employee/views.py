from django.db.models import ProtectedError, Q
from django.http import Http404
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


from employee.filters import (
    DisciplinaryActionFilter,
    DocumentRequestFilter,
    EmployeeFilter,
)
from employee.models import (
    Actiontype,
    DisciplinaryAction,
    Employee,
    EmployeeBankDetails,
    EmployeeType,
    EmployeeWorkInformation,
    Policy,
)
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
    EmployeeWorkInformationSerializer,
    PolicySerializer,
)



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
    Retrieves employee types.

    Methods:
        get(request, pk=None): Returns a single employee type if pk is provided, otherwise returns all employee types.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            employee_type = EmployeeType.objects.get(id=pk)
            serializer = EmployeeTypeSerializer(employee_type)
            return Response(serializer.data, status=200)
        employee_type = EmployeeType.objects.all()
        serializer = EmployeeTypeSerializer(employee_type, many=True)
        return Response(serializer.data, status=200)


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
        employees_queryset = Employee.objects.all()
        employees_filter_queryset = self.filterset_class(
            request.GET, queryset=employees_queryset
        ).qs
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


class EmployeeWorkInfoImportView(APIView):
    """
    Endpoint for importing employee work information.

    Methods:
        get(request):
            - Handles the importing of work information data based on user permissions.
    """

    permission_classes = [IsAuthenticated]

    @manager_permission_required("employee.add_employeeworkinformation")
    def get(self, request):
        return work_info_import(request)


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

    def post(self, request):
        if permission_check(request, "employee.add_policy") is False:
            return Response({"error": "No permission"}, status=401)

        serializer = PolicySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, pk):
        if permission_check(request, "employee.change_policy") is False:
            return Response({"error": "No permission"}, status=401)
        policy = self.get_object(pk)
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
        policy.delete()
        return Response({"message": "Policy deleted"}, status=200)
      except Http404:
        return Response({"error": "Policy not found"}, status=404)
      except Exception as e:
        # Log the error for debugging
        print("Delete Policy Error:", str(e))
        return Response({"error": str(e)}, status=500)
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
        document_request = self.get_object(pk)
        document_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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

class EmployeeBulkArchiveView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("employee.delete_employee"))
    def post(self, request, is_active):
        ids = request.data.get("ids")
        error = []
        for employee_id in ids:
            employee = Employee.objects.get(id=employee_id)
            employee.is_active = is_active
            employee.employee_user_id.is_active = is_active
            if employee.get_archive_condition() is False:
                employee.save()
            error.append(
                {
                    "employee": str(employee),
                    "error": "Related model found for this employee. ",
                }
            )
        return Response(error, status=200)


class EmployeeArchiveView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(permission_required("employee.delete_employee"))
    def post(self, request, id, is_active):
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


class EmployeeSelectorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        employee = user.employee_get
        
        # Determine user's role using RoleManager
        user_role = RoleManager.get_user_role(user, employee)
        
        # Get employees based on role
        employees = RoleManager.get_employees_by_role(user, employee, user_role)
        
        # Apply additional filters
        employees = self.apply_filters(request, employees)
        
        # Add role information to response
        response_data = {
            "user_role": user_role,
            "total_employees": employees.count(),
            "role_description": RoleManager.get_role_description(user_role)
        }
        
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(employees, request)
        serializer = EmployeeSelectorSerializer(page, many=True)
        
        # Combine pagination data with role information
        paginated_response = paginator.get_paginated_response(serializer.data)
        paginated_response.data.update(response_data)
        
        return paginated_response

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
        
        # Get user's role and employees using RoleManager
        user_role = RoleManager.get_user_role(user, employee)
        employees = RoleManager.get_employees_by_role(user, employee, user_role)
        
        # Get dashboard data based on role
        dashboard_data = self.get_dashboard_data(user, employee, user_role, employees)
        
        return Response(dashboard_data, status=200)

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
        
        # Get user's role and employees using RoleManager
        user_role = RoleManager.get_user_role(user, employee)
        employees = RoleManager.get_employees_by_role(user, employee, user_role)
        
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
