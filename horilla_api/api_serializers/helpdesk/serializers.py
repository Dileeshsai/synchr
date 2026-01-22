from rest_framework import serializers
from helpdesk.models import (
    Ticket,
    TicketType,
    Comment,
    Attachment,
    FAQ,
    FAQCategory,
    DepartmentManager,
    ClaimRequest,
)


class TicketTypeSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company_id.company", read_only=True
    )
    
    class Meta:
        model = TicketType
        fields = "__all__"


class TicketSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    ticket_type_title = serializers.CharField(
        source="ticket_type.title", read_only=True
    )
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = Ticket
        fields = "__all__"


class CommentSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    ticket_title = serializers.CharField(
        source="ticket.title", read_only=True
    )
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = Comment
        fields = "__all__"


class AttachmentSerializer(serializers.ModelSerializer):
    ticket_title = serializers.CharField(
        source="ticket.title", read_only=True
    )
    
    class Meta:
        model = Attachment
        fields = "__all__"


class FAQCategorySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company_id.company", read_only=True
    )
    
    class Meta:
        model = FAQCategory
        fields = "__all__"


class FAQSerializer(serializers.ModelSerializer):
    category_title = serializers.CharField(
        source="category.title", read_only=True
    )
    company_name = serializers.CharField(
        source="company_id.company", read_only=True
    )
    
    class Meta:
        model = FAQ
        fields = "__all__"


class DepartmentManagerSerializer(serializers.ModelSerializer):
    manager_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(
        source="department.department", read_only=True
    )
    
    def get_manager_name(self, obj):
        if obj.manager:
            return obj.manager.get_full_name()
        return None
    
    class Meta:
        model = DepartmentManager
        fields = "__all__"


class ClaimRequestSerializer(serializers.ModelSerializer):
    ticket_title = serializers.CharField(
        source="ticket_id.title", read_only=True
    )
    employee_name = serializers.SerializerMethodField()
    
    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee_id.get_full_name()
        return None
    
    class Meta:
        model = ClaimRequest
        fields = "__all__"

