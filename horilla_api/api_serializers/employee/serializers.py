from rest_framework import serializers

from base.models import Department, EmployeeType, JobPosition
from employee.models import (
    Actiontype,
    DisciplinaryAction,
    Employee,
    EmployeeBankDetails,
    EmployeeTag,
    EmployeeWorkInformation,
    Policy,
)
from horilla_documents.models import Document, DocumentRequest

from ...api_methods.employee.methods import get_next_badge_id


class ActiontypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actiontype
        # Expose block_option as well so frontend can manage
        # "Block login access" without affecting other behavior.
        fields = ["id", "title", "action_type", "block_option"]


class EmployeeListSerializer(serializers.ModelSerializer):
    job_position_name = serializers.CharField(
        source="employee_work_info.job_position_id.job_position", read_only=True
    )
    employee_work_info_id = serializers.CharField(
        source="employee_work_info.id", read_only=True
    )
    employee_bank_details_id = serializers.CharField(
        source="employee_bank_details.id", read_only=True
    )

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_first_name",
            "employee_last_name",
            "email",
            "job_position_name",
            "employee_work_info_id",
            "employee_profile",
            "employee_bank_details_id",
        ]


class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source="employee_work_info.department_id.department", read_only=True
    )
    department_id = serializers.CharField(
        source="employee_work_info.department_id.id", read_only=True
    )
    job_position_name = serializers.CharField(
        source="employee_work_info.job_position_id.job_position", read_only=True
    )
    job_position_id = serializers.CharField(
        source="employee_work_info.job_position_id.id", read_only=True
    )
    employee_work_info_id = serializers.CharField(
        source="employee_work_info.id", read_only=True
    )
    employee_bank_details_id = serializers.CharField(
        source="employee_bank_details.id", read_only=True
    )

    class Meta:
        model = Employee
        fields = "__all__"

    def create(self, validated_data):
        validated_data["badge_id"] = get_next_badge_id()
        return super().create(validated_data)


class EmployeeWorkInformationSerializer(serializers.ModelSerializer):
    job_position_name = serializers.CharField(
        source="job_position_id.job_position", read_only=True
    )
    department_name = serializers.CharField(
        source="department_id.department", read_only=True
    )
    shift_name = serializers.CharField(source="shift_id.employee_shift", read_only=True)
    employee_type_name = serializers.CharField(
        source="employee_type_id.employee_type", read_only=True
    )
    employee_first_name = serializers.CharField(
        source="employee_id.employee_first_name", read_only=True
    )
    employee_last_name = serializers.CharField(
        source="employee_id.employee_last_name", read_only=True
    )
    reporting_manager_first_name = serializers.CharField(
        source="reporting_manager_id.employee_first_name", read_only=True
    )
    reporting_manager_last_name = serializers.CharField(
        source="reporting_manager_id.employee_last_name", read_only=True
    )
    work_type_name = serializers.CharField(
        source="work_type_id.work_type", read_only=True
    )
    company_name = serializers.CharField(source="company_id.company", read_only=True)
    tags = serializers.SerializerMethodField()

    def get_tags(self, obj):
        return [
            {"id": tag.id, "title": tag.title, "color": tag.color}
            for tag in obj.tags.all()
        ]

    class Meta:
        model = EmployeeWorkInformation
        fields = "__all__"


class EmployeeBankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeBankDetails
        fields = "__all__"


class EmployeeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeType
        fields = "__all__"


class EmployeeTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeTag
        fields = "__all__"


class EmployeeBulkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        # fields = [
        #     'employee_last_name',
        #     'address',
        #     'country',
        #     'state',
        #     'city',
        #     'zip',
        #     'dob',
        #     'gender',
        #     'qualification',
        #     'experience',
        #     'marital_status',
        #     'children',
        # ]
        fields = [
            "employee_last_name",
        ]


class DisciplinaryActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisciplinaryAction
        fields = "__all__"


class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = "__all__"


class DocumentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentRequest
        fields = "__all__"


class DocumentSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    document_request_title = serializers.SerializerMethodField()
    document_request_description = serializers.SerializerMethodField()
    document_request_format = serializers.SerializerMethodField()
    document_request_max_size = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = "__all__"

    def get_employee_name(self, obj):
        try:
            return obj.employee_id.get_full_name()
        except Exception:
            return ""

    def get_document_request_title(self, obj):
        try:
            return obj.document_request_id.title if obj.document_request_id else ""
        except Exception:
            return ""

    def get_document_request_description(self, obj):
        try:
            return obj.document_request_id.description or "" if obj.document_request_id else ""
        except Exception:
            return ""

    def get_document_request_format(self, obj):
        try:
            return obj.document_request_id.format if obj.document_request_id else None
        except Exception:
            return None

    def get_document_request_max_size(self, obj):
        try:
            return obj.document_request_id.max_size if obj.document_request_id else None
        except Exception:
            return None


class EmployeeSelectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_first_name",
            "employee_last_name",
            "badge_id",
            "employee_profile",
        ]
