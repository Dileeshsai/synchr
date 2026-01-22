from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

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

from ...api_serializers.helpdesk.serializers import (
    TicketSerializer,
    TicketTypeSerializer,
    CommentSerializer,
    AttachmentSerializer,
    FAQSerializer,
    FAQCategorySerializer,
    DepartmentManagerSerializer,
    ClaimRequestSerializer,
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


TicketAPIView = create_crud_view(Ticket, TicketSerializer, "Ticket")
TicketTypeAPIView = create_crud_view(TicketType, TicketTypeSerializer, "TicketType")
CommentAPIView = create_crud_view(Comment, CommentSerializer, "Comment")
AttachmentAPIView = create_crud_view(Attachment, AttachmentSerializer, "Attachment")
FAQAPIView = create_crud_view(FAQ, FAQSerializer, "FAQ")
FAQCategoryAPIView = create_crud_view(FAQCategory, FAQCategorySerializer, "FAQCategory")
DepartmentManagerAPIView = create_crud_view(DepartmentManager, DepartmentManagerSerializer, "DepartmentManager")
ClaimRequestAPIView = create_crud_view(ClaimRequest, ClaimRequestSerializer, "ClaimRequest")

