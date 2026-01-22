from rest_framework import serializers
from onboarding.models import (
    OnboardingStage,
    OnboardingTask,
    CandidateStage,
    CandidateTask,
    OnboardingPortal,
)


class OnboardingStageSerializer(serializers.ModelSerializer):
    recruitment_title = serializers.CharField(
        source="recruitment_id.title", read_only=True
    )
    
    class Meta:
        model = OnboardingStage
        fields = "__all__"


class OnboardingTaskSerializer(serializers.ModelSerializer):
    stage_title = serializers.CharField(
        source="stage_id.stage_title", read_only=True
    )
    
    class Meta:
        model = OnboardingTask
        fields = "__all__"


class CandidateStageSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="candidate_id.name", read_only=True
    )
    stage_title = serializers.CharField(
        source="onboarding_stage_id.stage_title", read_only=True
    )
    
    class Meta:
        model = CandidateStage
        fields = "__all__"


class CandidateTaskSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="candidate_id.name", read_only=True
    )
    task_title = serializers.CharField(
        source="onboarding_task_id.task_title", read_only=True
    )
    stage_title = serializers.CharField(
        source="stage_id.stage_title", read_only=True
    )
    
    class Meta:
        model = CandidateTask
        fields = "__all__"


class OnboardingPortalSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="candidate_id.name", read_only=True
    )
    
    class Meta:
        model = OnboardingPortal
        fields = "__all__"

