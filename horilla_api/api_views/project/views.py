import calendar
import datetime

from django.db.models import ProtectedError, Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from project.models import Project, ProjectStage, Task, TimeSheet

from ...api_serializers.project.serializers import (
    ProjectSerializer,
    ProjectStageSerializer,
    TaskSerializer,
    TimeSheetSerializer,
)


def create_crud_view(model_class, serializer_class, model_name):
    """Helper function to create CRUD views"""
    class CRUDView(APIView):
        permission_classes = [IsAuthenticated]

        def get(self, request, pk=None):
            if pk:
                try:
                    obj = model_class.objects.get(pk=pk)
                    serializer = serializer_class(obj)
                    return Response(serializer.data, status=200)
                except model_class.DoesNotExist:
                    return Response(
                        {"error": f"{model_name} not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            paginator = PageNumberPagination()
            queryset = model_class.objects.all()
            page = paginator.paginate_queryset(queryset, request)
            serializer = serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        def post(self, request):
            serializer = serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        def put(self, request, pk):
            try:
                obj = model_class.objects.get(pk=pk)
                serializer = serializer_class(obj, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=200)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except model_class.DoesNotExist:
                return Response(
                    {"error": f"{model_name} not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        def delete(self, request, pk):
            try:
                obj = model_class.objects.get(pk=pk)
                obj.delete()
                return Response(
                    {"message": f"{model_name} deleted successfully"},
                    status=status.HTTP_200_OK,
                )
            except model_class.DoesNotExist:
                return Response(
                    {"error": f"{model_name} not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except ProtectedError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return CRUDView


ProjectAPIView = create_crud_view(Project, ProjectSerializer, "Project")
ProjectStageAPIView = create_crud_view(ProjectStage, ProjectStageSerializer, "ProjectStage")
TaskAPIView = create_crud_view(Task, TaskSerializer, "Task")
TimeSheetAPIView = create_crud_view(TimeSheet, TimeSheetSerializer, "TimeSheet")


class TasksMyAPIView(APIView):
    """
    Returns tasks where the current user's employee is task_manager or task_member.
    Aligns with tasks-list-individual-view. Supports project, stage, status query params.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = getattr(request.user, "employee_get", None)
        if not employee:
            queryset = Task.objects.none()
        else:
            queryset = Task.objects.filter(
                Q(task_managers=employee) | Q(task_members=employee)
            ).distinct().order_by("-id")
            project_id = request.query_params.get("project")
            if project_id:
                queryset = queryset.filter(project_id=project_id)
            stage_id = request.query_params.get("stage")
            if stage_id:
                queryset = queryset.filter(stage_id=stage_id)
            status = request.query_params.get("status")
            if status:
                queryset = queryset.filter(status=status)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = TaskSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProjectsDueInMonthAPIView(APIView):
    """
    Returns projects with end_date in the current month, excluding expired.
    Aligns with dashboard projects-due-in-this-month logic.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = datetime.date.today()
        first_day = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        last_day_of_month = today.replace(day=last_day)
        queryset = Project.objects.filter(
            Q(end_date__gte=first_day) & Q(end_date__lte=last_day_of_month)
        ).exclude(status="expired").order_by("end_date")
        serializer = ProjectSerializer(queryset, many=True)
        return Response(serializer.data, status=200)

