"""
API views for Mail Automations
"""

import json
import os

from django.conf import settings
from django.core import serializers as django_serializers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.models import HorillaMailTemplate
from horilla_automations.filters import AutomationFilter
from horilla_automations.methods.methods import generate_choices
from horilla_automations.methods.serialize import serialize_form
from horilla_automations.models import MailAutomation
from horilla_automations.signals import REFRESH_METHODS

from ...api_serializers.horilla_automations.serializers import (
    MailAutomationListSerializer,
    MailAutomationSerializer,
)


class MailAutomationView(APIView):
    """CRUD for MailAutomation"""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AutomationFilter

    def get_queryset(self):
        return MailAutomation.objects.all()

    def get_automation(self, pk):
        try:
            return MailAutomation.objects.get(pk=pk)
        except MailAutomation.DoesNotExist:
            return None

    def get(self, request, pk=None):
        if pk:
            automation = self.get_automation(pk)
            if not automation:
                return Response(
                    {"error": "Automation not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = MailAutomationSerializer(automation)
            return Response(serializer.data)
        queryset = self.get_queryset()
        filterset = self.filterset_class(request.GET, queryset=queryset)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(filterset.qs, request)
        serializer = MailAutomationListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        if not request.user.has_perm("horilla_automations.add_mailautomation"):
            return Response(
                {"error": "You do not have permission to add automations."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = MailAutomationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        if not request.user.has_perm("horilla_automations.change_mailautomation"):
            return Response(
                {"error": "You do not have permission to change automations."},
                status=status.HTTP_403_FORBIDDEN,
            )
        automation = self.get_automation(pk)
        if not automation:
            return Response(
                {"error": "Automation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = MailAutomationSerializer(automation, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not request.user.has_perm("horilla_automations.delete_mailautomation"):
            return Response(
                {"error": "You do not have permission to delete automations."},
                status=status.HTTP_403_FORBIDDEN,
            )
        automation = self.get_automation(pk)
        if not automation:
            return Response(
                {"error": "Automation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        automation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MailAutomationModelChoicesView(APIView):
    """GET model choices for MailAutomation.model field"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm("horilla_automations.view_mailautomation"):
            return Response(
                {"error": "You do not have permission to view automations."},
                status=status.HTTP_403_FORBIDDEN,
            )
        from horilla_automations.models import MODEL_CHOICES

        choices = [{"value": value, "label": label} for value, label in MODEL_CHOICES]
        return Response({"choices": choices})


class MailAutomationGetToFieldView(APIView):
    """GET mail_to choices and serialized form for condition builder by model path"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_perm("horilla_automations.view_mailautomation"):
            return Response(
                {"error": "You do not have permission to view automations."},
                status=status.HTTP_403_FORBIDDEN,
            )
        model_path = request.GET.get("model")
        if not model_path:
            return Response(
                {"error": "model query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            from django import forms

            to_fields, mail_details_choice, model_class = generate_choices(model_path)

            class InstantModelForm(forms.ModelForm):
                class Meta:
                    model = model_class
                    fields = "__all__"

            serialized_form = serialize_form(InstantModelForm(), "automation_multiple_")

            choices = [{"value": v, "label": l} for v, l in to_fields]
            mail_details = [{"value": v, "label": l} for v, l in mail_details_choice]

            return Response(
                {
                    "choices": choices,
                    "mail_details_choice": mail_details,
                    "serialized_form": serialized_form,
                }
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MailAutomationLoadView(APIView):
    """GET list of loadable automations from JSON fixtures; POST import selected"""

    permission_classes = [IsAuthenticated]

    template_file = os.path.join(settings.BASE_DIR, "load_data", "mail_templates.json")
    automation_file = os.path.join(
        settings.BASE_DIR, "load_data", "mail_automations.json"
    )

    def load_json_files(self):
        if not os.path.exists(self.template_file) or not os.path.exists(
            self.automation_file
        ):
            return None, None
        with open(self.template_file, "r", encoding="utf-8") as tf:
            templates_raw = json.load(tf)
        with open(self.automation_file, "r", encoding="utf-8") as af:
            automations_raw = json.load(af)
        return templates_raw, automations_raw

    def get(self, request):
        if not request.user.has_perm("horilla_automations.add_mailautomation"):
            return Response(
                {"error": "You do not have permission to add automations."},
                status=status.HTTP_403_FORBIDDEN,
            )
        templates_raw, automations_raw = self.load_json_files()
        if templates_raw is None:
            return Response(
                {"error": "Load data files not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        template_lookup = {
            item["pk"]: item["fields"]["body"] for item in templates_raw
        }
        processed = []
        for automation in automations_raw:
            p = {
                "pk": automation["pk"],
                "fields": automation["fields"],
                "template_body": template_lookup.get(
                    automation["fields"].get("mail_template"), ""
                ),
            }
            processed.append(p)
        return Response({"automations": processed})

    def post(self, request):
        if not request.user.has_perm("horilla_automations.add_mailautomation"):
            return Response(
                {"error": "You do not have permission to add automations."},
                status=status.HTTP_403_FORBIDDEN,
            )
        templates_raw, automations_raw = self.load_json_files()
        if templates_raw is None:
            return Response(
                {"error": "Load data files not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        selected_ids = request.data.get("ids", [])
        if not isinstance(selected_ids, list):
            selected_ids = [int(k) for k in selected_ids.split(",") if str(k).isdigit()]
        else:
            selected_ids = [int(x) for x in selected_ids if str(x).isdigit()]
        selected_automations = [a for a in automations_raw if a["pk"] in selected_ids]
        template_lookup = {
            item["pk"]: item["fields"]["body"] for item in templates_raw
        }
        required_template_pks = {
            a["fields"].get("mail_template")
            for a in selected_automations
            if a["fields"].get("mail_template")
        }
        from horilla_automations import models as automation_models

        imported = []
        skipped = []
        for template_json in templates_raw:
            if template_json["pk"] in required_template_pks:
                template_data = list(
                    django_serializers.deserialize(
                        "json", json.dumps([template_json])
                    )
                )[0].object
                existing = HorillaMailTemplate.objects.filter(
                    title=template_data.title
                ).first()
                if not existing:
                    template_data.pk = None
                    template_data.save()
        for automation_json in selected_automations:
            deserialized = list(
                django_serializers.deserialize(
                    "json", json.dumps([automation_json])
                )
            )[0]
            automation_obj = deserialized.object
            template_pk = automation_json["fields"].get("mail_template")
            template_body = template_lookup.get(template_pk)
            mail_template = HorillaMailTemplate.objects.filter(
                body=template_body
            ).first()
            automation_obj.mail_template = mail_template
            if not automation_models.MailAutomation.objects.filter(
                title=automation_obj.title
            ).exists():
                automation_obj.pk = None
                automation_obj.save()
                imported.append(automation_obj.title)
            else:
                skipped.append(automation_obj.title)
        return Response(
            {"imported": imported, "skipped": skipped},
            status=status.HTTP_200_OK,
        )


class MailAutomationRefreshView(APIView):
    """POST to refresh automation signals"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.has_perm("horilla_automations.add_mailautomation"):
            return Response(
                {"error": "You do not have permission to refresh automations."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            REFRESH_METHODS["clear_connection"]()
            REFRESH_METHODS["start_connection"]()
            return Response({"message": "Automations refreshed successfully"})
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
