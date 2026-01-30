import datetime
import django.utils.timezone

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from base.models import (
    AttendanceAllowedIP,
    BiometricAttendance,
    Company,
    Department,
    EmployeeShift,
    EmployeeShiftDay,
    EmployeeShiftSchedule,
    JobPosition,
    JobRole,
    RotatingShift,
    RotatingShiftAssign,
    RotatingWorkType,
    RotatingWorkTypeAssign,
    ShiftRequest,
    WorkType,
    WorkTypeRequest,
    WorkTypeRequestComment,
)
from horilla import horilla_middlewares


class BiometricAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiometricAttendance
        fields = ["id", "is_installed", "company_id"]
        read_only_fields = ["id", "company_id"]


class AttendanceAllowedIPSerializer(serializers.ModelSerializer):
    """
    Expose AttendanceAllowedIP as:
    - is_enabled: bool
    - allowed_ips: list of strings (maps to additional_data.allowed_ips)
    """

    allowed_ips = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )

    class Meta:
        model = AttendanceAllowedIP
        fields = ["id", "is_enabled", "allowed_ips"]
        read_only_fields = ["id"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["allowed_ips"] = instance.additional_data.get("allowed_ips", [])
        return data

    def update(self, instance, validated_data):
        allowed_ips = validated_data.pop("allowed_ips", None)
        if allowed_ips is not None:
            instance.additional_data = {"allowed_ips": allowed_ips}
        instance.is_enabled = validated_data.get("is_enabled", instance.is_enabled)
        # Use model clean() for validation (valid IPs/networks)
        instance.clean()
        instance.save()
        return instance

    def create(self, validated_data):
        allowed_ips = validated_data.pop("allowed_ips", [])
        instance = AttendanceAllowedIP.objects.create(
            is_enabled=validated_data.get("is_enabled", False),
            additional_data={"allowed_ips": allowed_ips},
        )
        instance.clean()
        instance.save()
        return instance


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


class JobPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPosition
        fields = "__all__"


class JobRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRole
        fields = "__all__"



class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"

    def create(self, validated_data):
        comapny_id = validated_data.pop("company_id", [])
        obj = Department(**validated_data)
        obj.save()
        obj.company_id.set(comapny_id)
        return obj


class WorkTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkType
        fields = "__all__"

    def validate(self, attrs):
        # Create an instance of the model with the provided data
        instance = WorkType(**attrs)

        # Call the model's clean method for validation
        try:
            instance.clean()
        except DjangoValidationError as e:
            # Raise DRF's ValidationError with the same message
            raise serializers.ValidationError(e)

        return attrs

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.clean()  # Call clean method before saving the instance
        instance.save()
        return instance


class RotatingWorkTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RotatingWorkType
        fields = "__all__"

    def validate(self, attrs):
        # Create an instance of the model with the provided data
        instance = RotatingWorkType(**attrs)

        # Call the model's clean method for validation
        try:
            instance.clean()
        except DjangoValidationError as e:
            # Raise DRF's ValidationError with the same message
            raise serializers.ValidationError(e)

        return attrs

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.clean()  # Call clean method before saving the instance
        instance.save()
        return instance


class RotatingWorkTypeAssignSerializer(serializers.ModelSerializer):
    rotating_work_type_name = serializers.SerializerMethodField(read_only=True)
    current_work_type_name = serializers.SerializerMethodField(read_only=True)
    next_work_type_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RotatingWorkTypeAssign
        fields = "__all__"

    def get_current_work_type_name(self, instance):
        current_work_type = instance.current_work_type
        if current_work_type:
            return current_work_type.work_type
        else:
            return None  # Return null if previous_work_type_id doesn't exist

    def get_next_work_type_name(self, instance):
        next_work_type = instance.next_work_type
        if next_work_type:
            return next_work_type.work_type
        else:
            return None  # Return null if previous_work_type_id doesn't exist

    def get_rotating_work_type_name(self, instance):
        rotating_work_type_id = instance.rotating_work_type_id
        if rotating_work_type_id:
            return rotating_work_type_id.name
        else:
            return None  # Return null if previous_work_type_id doesn't exist

    def validate(self, attrs):
        if self.instance:
            return attrs
        # Create an instance of the model with the provided data
        instance = RotatingWorkTypeAssign(**attrs)
        # Call the model's clean method for validation
        try:
            instance.clean()
        except DjangoValidationError as e:
            # Raise DRF's ValidationError with the same message
            raise serializers.ValidationError(e)
        return attrs

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class EmployeeShiftDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeShiftDay
        fields = "__all__"


class EmployeeShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeShift
        fields = "__all__"

    def validate(self, attrs):
        # Create an instance of the model with the provided data
        instance = EmployeeShift(**attrs)

        # Call the model's clean method for validation
        try:
            instance.clean()
        except DjangoValidationError as e:
            # Raise DRF's ValidationError with the same message
            raise serializers.ValidationError(e)

        return attrs

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.clean()  # Call clean method before saving the instance
        instance.save()
        return instance


class EmployeeShiftScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeShiftSchedule
        fields = "__all__"


class RotatingShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = RotatingShift
        fields = "__all__"

    def validate(self, attrs):
        # Create an instance of the model with the provided data
        instance = RotatingShift(**attrs)

        # Call the model's clean method for validation
        try:
            instance.clean()
        except DjangoValidationError as e:
            # Raise DRF's ValidationError with the same message
            raise serializers.ValidationError(e)

        return attrs

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.clean()  # Call clean method before saving the instance
        instance.save()
        return instance


class RotatingShiftAssignSerializer(serializers.ModelSerializer):
    current_shift_name = serializers.SerializerMethodField(read_only=True)
    next_shift_name = serializers.SerializerMethodField(read_only=True)
    rotating_shift_name = serializers.SerializerMethodField(read_only=True)
    rotate = serializers.CharField(read_only=True)

    class Meta:
        model = RotatingShiftAssign
        fields = "__all__"

    def validate(self, attrs):
        # Build instance for clean(): use existing pk on update so start_date >= today is not enforced for edits
        if self.instance:
            instance = RotatingShiftAssign(id=self.instance.pk, **attrs)
        else:
            instance = RotatingShiftAssign(**attrs)

        try:
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e)

        return attrs

    def create(self, validated_data):
        return super().create(validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.based_on == "after":
            representation["rotate"] = f"Rotate after {instance.rotate_after_day} days"
        elif instance.based_on == "weekly":
            representation["rotate"] = f"Weekly every {instance.rotate_every_weekend}"
        elif instance.based_on == "monthly":
            if instance.rotate_every == "1":
                representation["rotate"] = (
                    f"Rotate every {instance.rotate_every}st day of month"
                )
            elif instance.rotate_every == "2":
                representation["rotate"] = (
                    f"Rotate every {instance.rotate_every}nd day of month"
                )
            elif instance.rotate_every == "3":
                representation["rotate"] = (
                    f"Rotate every {instance.rotate_every}rd day of month"
                )
            elif instance.rotate_every == "last":
                representation["rotate"] = "Rotate every last day of month"
            else:
                representation["rotate"] = (
                    f"Rotate every {instance.rotate_every}th day of month"
                )

        return representation
    

    
    def get_rotating_shift_name(self, instance):
        rotating_shift_id = instance.rotating_shift_id
        if rotating_shift_id:
            return rotating_shift_id.name
        else:
            return None  # Return null if previous_work_type_id doesn't exist

    def get_next_shift_name(self, instance):
        next_shift = instance.next_shift
        if next_shift:
            return next_shift.employee_shift
        else:
            return None  # Return null if previous_work_type_id doesn't exist

    def get_current_shift_name(self, instance):
        current_shift = instance.current_shift
        if current_shift:
            return current_shift.employee_shift
        else:
            return None  # Return null if previous_work_type_id doesn't exist

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.clean()  # Call clean method before saving the instance
        instance.save()
        return instance


class WorkTypeRequestSerializer(serializers.ModelSerializer):
    employee_first_name = serializers.CharField(
        source="employee_id.employee_first_name", read_only=True
    )
    employee_last_name = serializers.CharField(
        source="employee_id.employee_last_name", read_only=True
    )
    work_type_name = serializers.CharField(
        source="work_type_id.work_type", read_only=True
    )
    previous_work_type_name = serializers.SerializerMethodField(read_only=True)
    comment = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = WorkTypeRequest
        fields = [
            f.name for f in WorkTypeRequest._meta.fields
        ] + ["employee_first_name", "employee_last_name", "work_type_name", "previous_work_type_name", "comment"]


    
    def validate(self, attrs):
     request = getattr(horilla_middlewares._thread_locals, "request", None)
    # Check if the user is not a superuser
     requested_date = attrs.get("requested_date", None)

     if request and not request.user.is_superuser:
        if requested_date and requested_date < datetime.datetime.today().date():
            raise serializers.ValidationError(
                {"requested_date": "Date must be greater than or equal to today."}
            )

    # Validate requested_till is not earlier than requested_date
     requested_till = attrs.get("requested_till", None)
     if requested_till and requested_till < requested_date:
        raise serializers.ValidationError(
            {
                "requested_till": (
                    "End date must be greater than or equal to start date."
                )
            }
        )

    # Only check for existing work type requests during CREATE, not UPDATE
     if not self.instance:
        # For creates only, create a new temporary instance
        temp_instance = WorkTypeRequest(
            employee_id=attrs.get("employee_id"),
            requested_date=requested_date,
            requested_till=requested_till,
            is_permanent_work_type=attrs.get("is_permanent_work_type", False)
        )
        if temp_instance.is_any_work_type_request_exists():
            raise serializers.ValidationError(
                {"error": "A work type request already exists during this time period."}
            )

    # Validate if `is_permanent_work_type` is False, `requested_till` must be provided
     if not attrs.get("is_permanent_work_type", False):
        if not requested_till:
            raise serializers.ValidationError(
                {"requested_till": ("Requested till field is required.")}
            )

     return attrs
    

    def create(self, validated_data):
        return super().create(validated_data)

    def get_previous_work_type_name(self, instance):
        previous_work_type = instance.previous_work_type_id
        if previous_work_type:
            return previous_work_type.work_type
        else:
            return None  # Return null if previous_work_type_id doesn't exist

    def get_comment(self, instance):
        comment_obj = (
            WorkTypeRequestComment.objects.filter(request_id=instance)
            .order_by("-id")
            .first()
        )
        return (comment_obj.comment or None) if comment_obj else None

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.clean()  # Call clean method before saving the instance
        instance.save()
        return instance

    

class ShiftRequestSerializer(serializers.ModelSerializer):
    employee_first_name = serializers.CharField(
        source="employee_id.employee_first_name", read_only=True
    )
    employee_last_name = serializers.CharField(
        source="employee_id.employee_last_name", read_only=True
    )
    shift_name = serializers.SerializerMethodField(read_only=True)
    previous_shift_name = serializers.SerializerMethodField(read_only=True)

    def get_previous_shift_name(self, instance):
        previous_shift_id = instance.previous_shift_id
        if previous_shift_id:
            return previous_shift_id.employee_shift
        else:
            return None  # Re

    def get_shift_name(self, instance):
        shift_id = instance.shift_id
        if shift_id:
            return shift_id.employee_shift
        else:
            return None  # Re

    def validate(self, attrs):
        # On update, use the existing instance so clean() can exclude current id in is_any_request_exists()
        if self.instance is not None:
            instance = self.instance
            for key, value in attrs.items():
                setattr(instance, key, value)
        else:
            instance = ShiftRequest(**attrs)

        # Call the model's clean method for validation
        try:
            instance.clean()
        except DjangoValidationError as e:
            # Raise DRF's ValidationError with the same message
            raise serializers.ValidationError(e)

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and hasattr(request.user, 'employee_get'):
            validated_data['employee_id'] = request.user.employee_get
        return super().create(validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.clean()  # Call clean method before saving the instance
        instance.save()
        return instance

    class Meta:
        model = ShiftRequest
        fields = "__all__"
