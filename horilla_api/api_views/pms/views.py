from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

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

from ...api_serializers.pms.serializers import (
    PeriodSerializer,
    KeyResultSerializer,
    ObjectiveSerializer,
    EmployeeObjectiveSerializer,
    EmployeeKeyResultSerializer,
    FeedbackSerializer,
    QuestionTemplateSerializer,
    QuestionSerializer,
    QuestionOptionsSerializer,
    AnswerSerializer,
    MeetingsSerializer,
    MeetingsAnswerSerializer,
    EmployeeBonusPointSerializer,
    BonusPointSettingSerializer,
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


PeriodAPIView = create_crud_view(Period, PeriodSerializer, "Period")
KeyResultAPIView = create_crud_view(KeyResult, KeyResultSerializer, "KeyResult")
ObjectiveAPIView = create_crud_view(Objective, ObjectiveSerializer, "Objective")
EmployeeObjectiveAPIView = create_crud_view(EmployeeObjective, EmployeeObjectiveSerializer, "EmployeeObjective")
EmployeeKeyResultAPIView = create_crud_view(EmployeeKeyResult, EmployeeKeyResultSerializer, "EmployeeKeyResult")
FeedbackAPIView = create_crud_view(Feedback, FeedbackSerializer, "Feedback")
QuestionTemplateAPIView = create_crud_view(QuestionTemplate, QuestionTemplateSerializer, "QuestionTemplate")
QuestionAPIView = create_crud_view(Question, QuestionSerializer, "Question")
QuestionOptionsAPIView = create_crud_view(QuestionOptions, QuestionOptionsSerializer, "QuestionOptions")
AnswerAPIView = create_crud_view(Answer, AnswerSerializer, "Answer")
MeetingsAPIView = create_crud_view(Meetings, MeetingsSerializer, "Meetings")
MeetingsAnswerAPIView = create_crud_view(MeetingsAnswer, MeetingsAnswerSerializer, "MeetingsAnswer")
EmployeeBonusPointAPIView = create_crud_view(EmployeeBonusPoint, EmployeeBonusPointSerializer, "EmployeeBonusPoint")
BonusPointSettingAPIView = create_crud_view(BonusPointSetting, BonusPointSettingSerializer, "BonusPointSetting")

