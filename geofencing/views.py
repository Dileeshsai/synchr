from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from geopy.distance import geodesic
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.models import Company
from geofencing.forms import GeoFencingSetupForm

from .models import GeoFencing
from .serializers import *


class GeoFencingSetupGetPostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Check if user has the specific permission, if not, allow if they're an employee
            if not request.user.has_perm("geofencing.view_geofencing"):
                # For mobile app users, allow access if they have an employee profile
                if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
                    return Response(
                        {"error": "No employee profile found for this user"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            company = request.user.employee_get.get_company()
            if not company:
                return Response(
                    {"error": "No company found for this employee"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                location = GeoFencing.objects.get(company_id=company)
                serializer = GeoFencingSetupSerializer(location)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except GeoFencing.DoesNotExist:
                return Response(
                    {"error": "Geofencing not configured for this company"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {"error": f"Error retrieving geofencing setup: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        try:
            # Check if user has the specific permission, if not, allow if they're an employee
            if not request.user.has_perm("geofencing.add_geofencing"):
                # For mobile app users, allow access if they have an employee profile
                if not hasattr(request.user, 'employee_get') or not request.user.employee_get:
                    return Response(
                        {"error": "No employee profile found for this user"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            data = request.data
            if not request.user.is_superuser:
                if isinstance(data, QueryDict):
                    data = data.dict()
                company = request.user.employee_get.get_company()
                if company:
                    data["company_id"] = company.id
            serializer = GeoFencingSetupSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Error creating geofencing setup: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GeoFencingSetupPutDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_location(self, pk):
        try:
            return GeoFencing.objects.get(pk=pk)
        except Exception as e:
            raise serializers.ValidationError(e)

    @method_decorator(
        permission_required("geofencing.change_geofencing", raise_exception=True),
        name="dispatch",
    )
    def put(self, request, pk):
        location = self.get_location(pk)
        company = request.user.employee_get.get_company()
        if request.user.is_superuser or company == location.company_id:
            serializer = GeoFencingSetupSerializer(
                location, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        raise serializers.ValidationError("Access Denied..")

    @method_decorator(
        permission_required("geofencing.delete_geofencing", raise_exception=True),
        name="dispatch",
    )
    def delete(self, request, pk):
        location = self.get_location(pk)
        company = request.user.employee_get.get_company()
        if request.user.is_superuser or company == location.company_id:
            location.delete()
            return Response(
                {"message": "GeoFencing location deleted successfully"},
                status=status.HTTP_200_OK,
            )
        raise serializers.ValidationError("Access Denied..")


class GeoFencingEmployeeLocationCheckAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_company(self, request):
        try:
            company = request.user.employee_get.get_company()
            return company
        except Exception as e:
            raise serializers.ValidationError(e)

    def get_company_location(self, request):
        company = self.get_company(request)
        try:
            location = GeoFencing.objects.get(company_id=company)
            return location
        except Exception as e:
            raise serializers.ValidationError(e)

    def post(self, request):
        serializer = EmployeeLocationSerializer(data=request.data)
        company_location = self.get_company_location(request)
        if company_location.start:
            if serializer.is_valid():
                geofence_center = (
                    company_location.latitude,
                    company_location.longitude,
                )
                employee_location = (
                    request.data.get("latitude"),
                    request.data.get("longitude"),
                )
                distance = geodesic(geofence_center, employee_location).meters
                if distance <= company_location.radius_in_meters:
                    return Response(
                        {"message": "Inside the geofence"}, status=status.HTTP_200_OK
                    )
                return Response(
                    {"message": "Outside the geofence"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        raise serializers.ValidationError("Geofencing is not yet started..")


class GeoFencingSetUpPermissionCheck(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(
        permission_required("geofencing.view_geofencing", raise_exception=True),
        name="dispatch",
    )
    def get(self, request):
        return Response(status=200)


def get_company(request):
    try:
        selected_company = request.session.get("selected_company")
        if selected_company == "all":
            return None
        company = Company.objects.get(id=selected_company)
        return company
    except Exception as e:
        raise serializers.ValidationError(e)


def get_company_location(request):
    company = get_company(request)
    try:
        location = GeoFencing.objects.get(company_id=company)
        return location
    except Exception as e:
        raise serializers.ValidationError(e)


@login_required
@permission_required("geofencing.add_localbackup")
def geo_location_config(request):
    try:
        form = GeoFencingSetupForm(instance=get_company_location(request))
    except:
        form = GeoFencingSetupForm()
    if request.method == "POST":
        try:
            form = GeoFencingSetupForm(
                request.POST, instance=get_company_location(request)
            )
        except:
            form = GeoFencingSetupForm(request.POST)
        if form.is_valid():
            geofencing = form.save(commit=False)
            geofencing.company_id = get_company(request)
            geofencing.save()
            messages.success(request, _("Geofencing config created successfully."))
        else:
            messages.info(request, "Not valid")
    return render(request, "geo_config.html", {"form": form})