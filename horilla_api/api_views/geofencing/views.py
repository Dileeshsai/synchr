from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from geofencing.models import GeoFencing
from ...api_serializers.geofencing.serializers import GeoFencingSerializer


class GeoFencingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            try:
                geofencing = GeoFencing.objects.get(pk=pk)
                serializer = GeoFencingSerializer(geofencing)
                return Response(serializer.data, status=200)
            except GeoFencing.DoesNotExist:
                return Response(
                    {"error": "GeoFencing not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        paginator = PageNumberPagination()
        geofencings = GeoFencing.objects.all()
        page = paginator.paginate_queryset(geofencings, request)
        serializer = GeoFencingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = GeoFencingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            geofencing = GeoFencing.objects.get(pk=pk)
            serializer = GeoFencingSerializer(geofencing, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=200)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except GeoFencing.DoesNotExist:
            return Response(
                {"error": "GeoFencing not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def delete(self, request, pk):
        try:
            geofencing = GeoFencing.objects.get(pk=pk)
            geofencing.delete()
            return Response(
                {"message": "GeoFencing deleted successfully"},
                status=status.HTTP_200_OK,
            )
        except GeoFencing.DoesNotExist:
            return Response(
                {"error": "GeoFencing not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ProtectedError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

