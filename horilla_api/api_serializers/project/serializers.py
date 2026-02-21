from rest_framework import serializers

from base.models import Company
from project.models import Project, ProjectStage, Task, TimeSheet


class ProjectSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company_id.company", read_only=True
    )
    # Model has company_id editable=False so DRF treats it read_only; override so API can set it
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Project
        fields = "__all__"


class ProjectStageSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(
        source="project.title", read_only=True
    )
    
    class Meta:
        model = ProjectStage
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(
        source="project.title", read_only=True
    )
    stage_title = serializers.CharField(
        source="stage.title", read_only=True
    )
    
    class Meta:
        model = Task
        fields = "__all__"


class TimeSheetSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(
        source="project_id.title", read_only=True
    )
    task_title = serializers.CharField(
        source="task_id.title", read_only=True
    )
    employee_name = serializers.SerializerMethodField()
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = TimeSheet
        fields = "__all__"

