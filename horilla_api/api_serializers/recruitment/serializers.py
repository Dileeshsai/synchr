from rest_framework import serializers
from recruitment.models import (
    Recruitment,
    Candidate,
    Stage,
    InterviewSchedule,
    SurveyTemplate,
    Skill,
    StageNote,
    RejectReason,
    RejectedCandidate,
    SkillZone,
    SkillZoneCandidate,
    CandidateRating,
    CandidateDocument,
    CandidateDocumentRequest,
    LinkedInAccount,
)


class RecruitmentSerializer(serializers.ModelSerializer):
    job_position_name = serializers.CharField(
        source="job_position_id.job_position", read_only=True
    )
    company_name = serializers.CharField(
        source="company_id.company", read_only=True
    )
    
    class Meta:
        model = Recruitment
        fields = "__all__"


class CandidateSerializer(serializers.ModelSerializer):
    recruitment_title = serializers.CharField(
        source="recruitment_id.title", read_only=True
    )
    stage_title = serializers.CharField(
        source="stage_id.stage", read_only=True
    )
    full_name = serializers.SerializerMethodField()
    
    def get_full_name(self, obj):
        return obj.get_full_name() if hasattr(obj, 'get_full_name') else f"{obj.name}"
    
    class Meta:
        model = Candidate
        fields = "__all__"


class StageSerializer(serializers.ModelSerializer):
    recruitment_title = serializers.CharField(
        source="recruitment_id.title", read_only=True
    )
    
    class Meta:
        model = Stage
        fields = "__all__"


class InterviewScheduleSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="candidate_id.name", read_only=True
    )
    employee_name = serializers.SerializerMethodField()
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = InterviewSchedule
        fields = "__all__"


class SurveyTemplateSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company_id.company", read_only=True
    )
    
    class Meta:
        model = SurveyTemplate
        fields = "__all__"


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = "__all__"


class StageNoteSerializer(serializers.ModelSerializer):
    stage_title = serializers.CharField(
        source="stage_id.stage", read_only=True
    )
    candidate_name = serializers.CharField(
        source="candidate_id.name", read_only=True
    )
    
    class Meta:
        model = StageNote
        fields = "__all__"


class RejectReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = RejectReason
        fields = "__all__"


class RejectedCandidateSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="candidate_id.name", read_only=True
    )
    reject_reason_title = serializers.CharField(
        source="reject_reason_id.title", read_only=True
    )
    
    class Meta:
        model = RejectedCandidate
        fields = "__all__"


class SkillZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillZone
        fields = "__all__"


class SkillZoneCandidateSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="candidate_id.name", read_only=True
    )
    skill_zone_title = serializers.CharField(
        source="skill_zone_id.title", read_only=True
    )
    
    class Meta:
        model = SkillZoneCandidate
        fields = "__all__"


class CandidateRatingSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="candidate_id.name", read_only=True
    )
    
    class Meta:
        model = CandidateRating
        fields = "__all__"


class CandidateDocumentSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="candidate_id.name", read_only=True
    )
    
    class Meta:
        model = CandidateDocument
        fields = "__all__"


class CandidateDocumentRequestSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="candidate_id.name", read_only=True
    )
    
    class Meta:
        model = CandidateDocumentRequest
        fields = "__all__"


class LinkedInAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkedInAccount
        fields = "__all__"

