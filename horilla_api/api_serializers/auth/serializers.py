from rest_framework import serializers

from employee.models import Employee
from django.contrib.auth import get_user_model


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class GetEmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    job_position = serializers.SerializerMethodField()
    shift = serializers.SerializerMethodField()
    reporting_manager = serializers.SerializerMethodField()
    work_type = serializers.SerializerMethodField()
    employee_type = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    leave_status = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            "id",
            "badge_id",
            "employee_user_id",
            "employee_first_name",
            "employee_last_name",
            "full_name",
            "employee_profile",
            "avatar",
            "email",
            "phone",
            "address",
            "country",
            "state",
            "city",
            "zip",
            "dob",
            "gender",
            "qualification",
            "experience",
            "marital_status",
            "children",
            "emergency_contact",
            "emergency_contact_name",
            "emergency_contact_relation",
            "is_active",
            "additional_info",
            "is_from_onboarding",
            "is_directly_converted",
            "department",
            "job_position",
            "shift",
            "reporting_manager",
            "work_type",
            "employee_type",
            "leave_status",
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_department(self, obj):
        dept = obj.get_department()
        return dept.department if dept else None

    def get_job_position(self, obj):
        pos = obj.get_job_position()
        return pos.job_position if pos else None

    def get_shift(self, obj):
        shift = obj.get_shift()
        return shift.shift_name if shift else None

    def get_reporting_manager(self, obj):
        mgr = obj.get_reporting_manager()
        return mgr.get_full_name() if mgr else None

    def get_work_type(self, obj):
        wt = obj.get_work_type()
        return wt.work_type if wt else None

    def get_employee_type(self, obj):
        et = obj.get_employee_type()
        return et.employee_type if et else None

    def get_avatar(self, obj):
        return obj.get_avatar()

    def get_leave_status(self, obj):
        return obj.get_leave_status()