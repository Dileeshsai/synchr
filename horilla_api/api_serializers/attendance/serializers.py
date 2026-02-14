from rest_framework import serializers

from attendance.models import *
from base.models import HorillaMailTemplate


class AttendanceSerializer(serializers.ModelSerializer):
    employee_first_name = serializers.CharField(
        source="employee_id.employee_first_name", read_only=True
    )
    employee_last_name = serializers.CharField(
        source="employee_id.employee_last_name", read_only=True
    )
    shift_name = serializers.CharField(source="shift_id.employee_shift", read_only=True)
    badge_id = serializers.CharField(source="employee_id.badge_id", read_only=True)
    employee_profile_url = serializers.SerializerMethodField(read_only=True)
    work_type = serializers.CharField(source="work_type_id.work_type", read_only=True)
    hours_pending = serializers.SerializerMethodField(read_only=True)
    batch_attendance_title = serializers.SerializerMethodField(read_only=True)
    attendance_overtime = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Attendance
        exclude = [
            "overtime_second",
            "at_work_second",
            "attendance_day",
            "request_description",
            "approved_overtime_second",
            "request_type",
            "requested_data",
            "is_validate_request",
            "is_validate_request_approved",
        ]

    def validate(self, data):
        # Check if attendance exists for the employee on the current date
        if self.instance:
            return data
        employee_id = data.get("employee_id")
        attendance_date = data.get("attendance_date", date.today())
        if Attendance.objects.filter(
            employee_id=employee_id, attendance_date=attendance_date
        ).exists():
            raise ValidationError(
                ("Attendance for this employee on the current date already exists.")
            )
        return data

    def get_employee_profile_url(self, obj):
        try:
            employee_profile = obj.employee_id.employee_profile
            return employee_profile.url
        except:
            return None

    def get_hours_pending(self, obj):
        try:
            return obj.hours_pending
        except Exception:
            return None

    def get_attendance_overtime(self, obj):
        try:
            return obj.attendance_overtime
        except Exception:
            return None

    def get_batch_attendance_title(self, obj):
        try:
            return obj.batch_attendance_id.title if obj.batch_attendance_id else None
        except Exception:
            return None


class AttendanceRequestSerializer(serializers.ModelSerializer):
    employee_first_name = serializers.CharField(
        source="employee_id.employee_first_name", read_only=True
    )
    employee_last_name = serializers.CharField(
        source="employee_id.employee_last_name", read_only=True
    )
    shift_name = serializers.CharField(source="shift_id.employee_shift", read_only=True)
    badge_id = serializers.CharField(source="employee_id.badge_id", read_only=True)
    employee_profile_url = serializers.SerializerMethodField(read_only=True)
    batch_attendance_title = serializers.SerializerMethodField(read_only=True)
    requested_fields = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Attendance
        exclude = [
            "attendance_overtime_approve",
            "approved_overtime_second",
            "is_validate_request",
            "is_validate_request_approved",
            "created_at",
        ]

    def create(self, validated_data):
        # Extract relevant data from validated_data
        employee_id = validated_data.get("employee_id")
        attendance_date = validated_data.get("attendance_date")
        # Check if attendance exists for the employee and date
        attendances = Attendance.objects.filter(
            employee_id=employee_id, attendance_date=attendance_date
        )
        data = {
            "employee_id": validated_data.get("employee_id"),
            "attendance_date": validated_data.get("attendance_date"),
            "attendance_clock_in_date": validated_data.get("attendance_clock_in_date"),
            "attendance_clock_in": validated_data.get("attendance_clock_in"),
            "attendance_clock_out": validated_data.get("attendance_clock_out"),
            "attendance_clock_out_date": validated_data.get(
                "attendance_clock_out_date"
            ),
            "shift_id": validated_data.get("shift_id"),
            "work_type_id": validated_data.get("work_type_id"),
            "attendance_worked_hour": validated_data.get("attendance_worked_hour"),
            "minimum_hour": validated_data.get("minimum_hour"),
        }
        if attendances.exists():
            data["employee_id"] = employee_id.id
            data["attendance_date"] = str(attendance_date)
            data["attendance_clock_in_date"] = self.data["attendance_clock_in_date"]
            data["attendance_clock_in"] = self.data["attendance_clock_in"]
            data["attendance_clock_out"] = (
                None
                if data["attendance_clock_out"] == "None"
                else data["attendance_clock_out"]
            )
            data["attendance_clock_out_date"] = (
                None
                if data["attendance_clock_out_date"] == "None"
                else data["attendance_clock_out_date"]
            )
            data["work_type_id"] = self.data["work_type_id"]
            data["shift_id"] = self.data["shift_id"]
            attendance = attendances.first()
            for key, value in data.items():
                data[key] = str(value)
            attendance.requested_data = json.dumps(data)
            attendance.is_validate_request = True
            if attendance.request_type != "create_request":
                attendance.request_type = "update_request"
            attendance.request_description = self.data["request_description"]
            return attendance.save()
        new_instance = Attendance(**data)
        new_instance.is_validate_request = True
        new_instance.attendance_validated = False
        new_instance.request_description = self.data["request_description"]
        new_instance.request_type = "create_request"
        new_instance.save()
        return new_instance

    def update(self, instance, validated_data):
        if "employee_id" in validated_data:
            validated_data.pop("employee_id")
        return super().update(instance, validated_data)

    
    def get_employee_profile_url(self, obj):
        try:
            employee_profile = obj.employee_id.employee_profile
            return employee_profile.url
        except:
            return None

    def get_batch_attendance_title(self, obj):
        try:
            return obj.batch_attendance_id.title if obj.batch_attendance_id else None
        except Exception:
            return None

    def get_requested_fields(self, obj):
        try:
            rf = obj.requested_fields
            return list(rf) if rf else []
        except Exception:
            return []


class AttendanceOverTimeSerializer(serializers.ModelSerializer):
    badge_id = serializers.CharField(source="employee_id.badge_id", read_only=True)
    employee_first_name = serializers.CharField(
        source="employee_id.employee_first_name", read_only=True
    )
    employee_last_name = serializers.CharField(
        source="employee_id.employee_last_name", read_only=True
    )
    employee_profile_url = serializers.SerializerMethodField(read_only=True)
    not_validated_hrs = serializers.SerializerMethodField(read_only=True)
    not_approved_ot_hrs = serializers.SerializerMethodField(read_only=True)
    month_index = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AttendanceOverTime
        fields = [
            "id",
            "employee_first_name",
            "employee_last_name",
            "employee_profile_url",
            "badge_id",
            "employee_id",
            "month",
            "year",
            "worked_hours",
            "pending_hours",
            "overtime",
            "not_validated_hrs",
            "not_approved_ot_hrs",
            "month_index",
        ]

    def get_employee_profile_url(self, obj):
        try:
            employee_profile = obj.employee_id.employee_profile
            return employee_profile.url
        except Exception:
            return None

    def get_not_validated_hrs(self, obj):
        try:
            return obj.not_validated_hrs()
        except Exception:
            return "00:00"

    def get_not_approved_ot_hrs(self, obj):
        try:
            return obj.not_approved_ot_hrs()
        except Exception:
            return "00:00"

    def get_month_index(self, obj):
        try:
            return obj.get_month_index()
        except Exception:
            return None


class AttendanceLateComeEarlyOutSerializer(serializers.ModelSerializer):
    employee_first_name = serializers.CharField(
        source="employee_id.employee_first_name", read_only=True
    )
    employee_last_name = serializers.CharField(
        source="employee_id.employee_last_name", read_only=True
    )
    attendance_date = serializers.DateField(
        source="attendance_id.attendance_date", read_only=True
    )
    attendance_clock_in_date = serializers.DateField(
        source="attendance_id.attendance_clock_in_date", read_only=True, allow_null=True
    )
    attendance_clock_in = serializers.TimeField(
        source="attendance_id.attendance_clock_in", read_only=True, allow_null=True
    )
    attendance_clock_out_date = serializers.DateField(
        source="attendance_id.attendance_clock_out_date", read_only=True, allow_null=True
    )
    attendance_clock_out = serializers.TimeField(
        source="attendance_id.attendance_clock_out", read_only=True, allow_null=True
    )
    minimum_hour = serializers.CharField(
        source="attendance_id.minimum_hour", read_only=True, allow_null=True
    )
    attendance_worked_hour = serializers.CharField(
        source="attendance_id.attendance_worked_hour", read_only=True, allow_null=True
    )
    penalties_count = serializers.SerializerMethodField()
    shift_name = serializers.SerializerMethodField()
    work_type_name = serializers.SerializerMethodField()
    attendance_validated = serializers.SerializerMethodField()

    def get_penalties_count(self, obj):
        return obj.get_penalties_count()

    def get_shift_name(self, obj):
        att = getattr(obj, "attendance_id", None)
        if att and hasattr(att, "shift_id") and att.shift_id:
            return str(att.shift_id)
        return None

    def get_work_type_name(self, obj):
        att = getattr(obj, "attendance_id", None)
        if att and hasattr(att, "work_type_id") and att.work_type_id:
            return str(att.work_type_id)
        return None

    def get_attendance_validated(self, obj):
        att = getattr(obj, "attendance_id", None)
        if att is not None and hasattr(att, "attendance_validated"):
            return att.attendance_validated
        return None

    class Meta:
        model = AttendanceLateComeEarlyOut
        fields = "__all__"


class AttendanceActivitySerializer(serializers.ModelSerializer):
    employee_first_name = serializers.CharField(
        source="employee_id.employee_first_name", read_only=True
    )
    employee_last_name = serializers.CharField(
        source="employee_id.employee_last_name", read_only=True
    )

    class Meta:
        model = AttendanceActivity
        fields = "__all__"


class AttendanceValidationConditionSerializer(serializers.ModelSerializer):
    """
    Serializer for AttendanceValidationCondition (attendance break-point / validation condition).
    """

    class Meta:
        model = AttendanceValidationCondition
        fields = [
            "id",
            "validation_at_work",
            "minimum_overtime_to_approve",
            "overtime_cutoff",
            "auto_approve_ot",
            "company_id",
            "created_at",
        ]


class AttendanceRequestCommentSerializer(serializers.ModelSerializer):
    """Serializer for attendance request comments (list/detail)."""

    employee = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceRequestComment
        fields = ["id", "comment", "created_at", "employee"]

    def get_employee(self, obj):
        emp = getattr(obj, "employee_id", None)
        if not emp:
            return None
        avatar = getattr(emp, "get_avatar", None)
        if callable(avatar):
            try:
                avatar = avatar()
            except Exception:
                avatar = None
        return {
            "id": emp.id,
            "full_name": emp.get_full_name() if hasattr(emp, "get_full_name") else str(emp),
            "avatar": avatar,
        }


class AttendanceRequestCommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating attendance request comments."""

    class Meta:
        model = AttendanceRequestComment
        fields = ["comment"]


class AttendanceGeneralSettingSerializer(serializers.ModelSerializer):
    """
    Serializer for AttendanceGeneralSetting (check in/check out settings).
    """
    company_name = serializers.CharField(
        source="company_id.company", read_only=True, allow_null=True
    )

    class Meta:
        model = AttendanceGeneralSetting
        fields = [
            "id",
            "time_runner",
            "enable_check_in",
            "company_id",
            "company_name",
            "created_at",
        ]


class GraceTimeSerializer(serializers.ModelSerializer):
    """
    Serializer for GraceTime (grace time settings).
    """

    allowed_time_in_secs = serializers.IntegerField(read_only=True)

    class Meta:
        model = GraceTime
        fields = [
            "id",
            "allowed_time",
            "allowed_time_in_secs",
            "allowed_clock_in",
            "allowed_clock_out",
            "is_default",
            "is_active",
            "company_id",
            "created_at",
        ]


class MailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorillaMailTemplate
        fields = "__all__"
