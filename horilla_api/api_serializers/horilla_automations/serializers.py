"""
Serializers for Mail Automation API
"""

import ast

from rest_framework import serializers

from base.models import HorillaMailTemplate
from employee.models import Employee
from horilla_automations.models import MailAutomation


class MailAutomationListSerializer(serializers.ModelSerializer):
    """Light serializer for list view"""

    trigger_display = serializers.CharField(source="get_trigger_display", read_only=True)
    delivery_channel_display = serializers.CharField(
        source="get_delivery_channel_display", read_only=True
    )
    mail_template_title = serializers.SerializerMethodField()
    mail_to_display = serializers.SerializerMethodField()

    class Meta:
        model = MailAutomation
        fields = [
            "id",
            "title",
            "model",
            "trigger",
            "trigger_display",
            "delivery_channel",
            "delivery_channel_display",
            "mail_template",
            "mail_template_title",
            "mail_to",
            "mail_to_display",
        ]

    def get_mail_template_title(self, obj):
        return obj.mail_template.title if obj.mail_template else None

    def get_mail_to_display(self, obj):
        """Return human-readable mail_to mapping strings for list display."""
        if not obj.mail_to:
            return []
        try:
            mail_to = ast.literal_eval(obj.mail_to)
            mappings = []
            for mapping in mail_to:
                parts = mapping.split("__")
                display = " > ".join(
                    p.replace("_id", "").replace("_", " ").capitalize() for p in parts
                )
                mappings.append(display)
            return mappings
        except (ValueError, SyntaxError):
            return []


class MailAutomationSerializer(serializers.ModelSerializer):
    """Full serializer for create/update/detail"""

    mail_template_title = serializers.SerializerMethodField()

    also_sent_to = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Employee.objects.all(), required=False
    )
    template_attachments = serializers.PrimaryKeyRelatedField(
        many=True, queryset=HorillaMailTemplate.objects.all(), required=False
    )
    mail_to = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = MailAutomation
        fields = [
            "id",
            "title",
            "model",
            "mail_to",
            "mail_details",
            "trigger",
            "mail_template",
            "mail_template_title",
            "also_sent_to",
            "delivery_channel",
            "template_attachments",
            "condition",
            "condition_html",
            "condition_querystring",
        ]
        extra_kwargs = {
            "condition_html": {"required": False, "allow_blank": True},
            "condition_querystring": {"required": False, "allow_blank": True},
        }
        read_only_fields = ["mail_template_title"]

    def get_mail_template_title(self, obj):
        return obj.mail_template.title if obj.mail_template else None

    def create(self, validated_data):
        validated_data = dict(validated_data)
        also_sent_to = validated_data.pop("also_sent_to", [])
        template_attachments = validated_data.pop("template_attachments", [])
        cond_html = validated_data.pop("condition_html", None)
        cond_qs = validated_data.pop("condition_querystring", None)
        instance = super().create(validated_data)
        if cond_html is not None:
            instance.condition_html = cond_html
        if cond_qs is not None:
            instance.condition_querystring = cond_qs
        if cond_html is not None or cond_qs is not None:
            instance.save(update_fields=["condition_html", "condition_querystring"])
        instance.also_sent_to.set(also_sent_to)
        instance.template_attachments.set(template_attachments)
        return instance

    def update(self, instance, validated_data):
        validated_data = dict(validated_data)
        also_sent_to = validated_data.pop("also_sent_to", None)
        template_attachments = validated_data.pop("template_attachments", None)
        cond_html = validated_data.pop("condition_html", None)
        cond_qs = validated_data.pop("condition_querystring", None)
        instance = super().update(instance, validated_data)
        update_fields = []
        if cond_html is not None:
            instance.condition_html = cond_html
            update_fields.append("condition_html")
        if cond_qs is not None:
            instance.condition_querystring = cond_qs
            update_fields.append("condition_querystring")
        if update_fields:
            instance.save(update_fields=update_fields)
        if also_sent_to is not None:
            instance.also_sent_to.set(also_sent_to)
        if template_attachments is not None:
            instance.template_attachments.set(template_attachments)
        return instance

    def to_representation(self, instance):
        """Parse mail_to from stored string to list for API response"""
        ret = super().to_representation(instance)
        if instance.mail_to:
            try:
                ret["mail_to"] = ast.literal_eval(instance.mail_to)
            except (ValueError, SyntaxError):
                ret["mail_to"] = []
        else:
            ret["mail_to"] = []
        return ret

    def to_internal_value(self, data):
        """Convert mail_to list to string for storage"""
        ret = super().to_internal_value(data)
        if "mail_to" in ret and isinstance(ret["mail_to"], list):
            ret["mail_to"] = str(ret["mail_to"])
        return ret
