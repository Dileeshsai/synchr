from rest_framework import serializers
from pms.models import (
    Period,
    KeyResult,
    Objective,
    EmployeeObjective,
    EmployeeKeyResult,
    Feedback,
    QuestionTemplate,
    Question,
    QuestionOptions,
    Answer,
    Meetings,
    MeetingsAnswer,
    EmployeeBonusPoint,
    BonusPointSetting,
)


class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        fields = "__all__"


class KeyResultSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company_id.company", read_only=True
    )
    
    class Meta:
        model = KeyResult
        fields = "__all__"


class ObjectiveSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company_id.company", read_only=True
    )
    
    class Meta:
        model = Objective
        fields = "__all__"


class EmployeeObjectiveSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    objective_title = serializers.CharField(
        source="objective_id.title", read_only=True
    )
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = EmployeeObjective
        fields = "__all__"


class EmployeeKeyResultSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    key_result_title = serializers.CharField(
        source="key_result_id.title", read_only=True
    )
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = EmployeeKeyResult
        fields = "__all__"


class QuestionTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionTemplate
        fields = "__all__"


class QuestionSerializer(serializers.ModelSerializer):
    template_title = serializers.CharField(
        source="template_id.title", read_only=True
    )
    
    class Meta:
        model = Question
        fields = "__all__"


class QuestionOptionsSerializer(serializers.ModelSerializer):
    question_title = serializers.CharField(
        source="question_id.question", read_only=True
    )
    
    class Meta:
        model = QuestionOptions
        fields = "__all__"


class FeedbackSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    review_cycle_name = serializers.CharField(
        source="review_cycle.period_name", read_only=True
    )
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = Feedback
        fields = "__all__"


class AnswerSerializer(serializers.ModelSerializer):
    question_title = serializers.CharField(
        source="question_id.question", read_only=True
    )
    employee_name = serializers.SerializerMethodField()
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = Answer
        fields = "__all__"


class MeetingsSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = Meetings
        fields = "__all__"


class MeetingsAnswerSerializer(serializers.ModelSerializer):
    meeting_title = serializers.CharField(
        source="meeting_id.title", read_only=True
    )
    employee_name = serializers.SerializerMethodField()
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = MeetingsAnswer
        fields = "__all__"


class EmployeeBonusPointSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = EmployeeBonusPoint
        fields = "__all__"


class BonusPointSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BonusPointSetting
        fields = "__all__"

