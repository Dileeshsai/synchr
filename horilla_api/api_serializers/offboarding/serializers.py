from rest_framework import serializers
from offboarding.models import (
    Offboarding,
    OffboardingStage,
    OffboardingEmployee,
    ResignationLetter,
    OffboardingTask,
    EmployeeTask,
    ExitReason,
    OffboardingNote,
    OffboardingGeneralSetting,
)


class OffboardingSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company_id.company", read_only=True
    )
    
    class Meta:
        model = Offboarding
        fields = "__all__"


class OffboardingStageSerializer(serializers.ModelSerializer):
    offboarding_title = serializers.CharField(
        source="offboarding_id.title", read_only=True
    )
    
    class Meta:
        model = OffboardingStage
        fields = "__all__"


class OffboardingEmployeeSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    stage_title = serializers.CharField(
        source="stage_id.title", read_only=True
    )
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = OffboardingEmployee
        fields = "__all__"


class ResignationLetterSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = ResignationLetter
        fields = "__all__"


class OffboardingTaskSerializer(serializers.ModelSerializer):
    stage_title = serializers.CharField(
        source="stage_id.title", read_only=True
    )
    
    class Meta:
        model = OffboardingTask
        fields = "__all__"


class EmployeeTaskSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    task_title = serializers.CharField(
        source="task_id.title", read_only=True
    )
    
    def get_employee_name(self, obj):
        if obj.employee_id and obj.employee_id.employee_id:
            return obj.employee_id.employee_id.get_full_name()
        return None
    
    class Meta:
        model = EmployeeTask
        fields = "__all__"


class ExitReasonSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    
    def get_employee_name(self, obj):
        if obj.offboarding_employee_id and obj.offboarding_employee_id.employee_id:
            return obj.offboarding_employee_id.employee_id.get_full_name()
        return None
    
    class Meta:
        model = ExitReason
        fields = "__all__"


class OffboardingNoteSerializer(serializers.ModelSerializer):
    note_by_name = serializers.SerializerMethodField()
    
    def get_note_by_name(self, obj):
        if obj.note_by:
            return obj.note_by.get_full_name()
        return None
    
    class Meta:
        model = OffboardingNote
        fields = "__all__"


class OffboardingGeneralSettingSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company_id.company", read_only=True
    )
    
    class Meta:
        model = OffboardingGeneralSetting
        fields = "__all__"

