import calendar
import io
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import pandas as pd
from django import template
from django.apps import apps
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import IntegrityError
from django.db.models import Case, CharField, F, Q, Value, When
from django.http import QueryDict
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from attendance.methods.utils import monthly_leave_days
from attendance.models import (
    Attendance,
    AttendanceActivity,
    AttendanceOverTime,
    AttendanceRequestComment,
    BatchAttendance,
    AttendanceGeneralSetting,
    AttendanceValidationCondition,
    EmployeeShiftDay,
    GraceTime,
    WorkRecords,
)
from attendance.views.clock_in_out import *
from attendance.views.clock_in_out import clock_out
from attendance.views.dashboard import (
    find_expected_attendances,
    find_early_out,
    find_late_come,
    find_on_time,
    generate_data_set,
    get_month_start_end_dates,
    get_week_start_end_dates,
    total_attendance,
)
from attendance.filters import AttendanceActivityFilter, AttendanceOverTimeFilter
from attendance.methods.utils import (
    get_diff_dict,
    pending_hour_data,
    strtime_seconds,
    worked_hour_data,
)
from base.models import Department, TrackLateComeEarlyOut
from attendance.forms import AttendanceActivityExportForm
from attendance.views.views import *
from base.backends import ConfiguredEmailBackend
from base.methods import (
    closest_numbers,
    filtersubordinates,
    filtersubordinatesemployeemodel,
    generate_pdf,
    get_pagination,
    is_reportingmanager,
)
from horilla.horilla_settings import HORILLA_DATE_FORMATS
from base.models import HorillaMailTemplate
from employee.filters import EmployeeFilter

from ...api_decorators.base.decorators import (
    manager_permission_required,
    permission_required,
)
from ...api_methods.base.methods import groupby_queryset, permission_based_queryset
from ...api_serializers.attendance.serializers import (
    AttendanceActivitySerializer,
    AttendanceGeneralSettingSerializer,
    AttendanceLateComeEarlyOutSerializer,
    AttendanceOverTimeSerializer,
    AttendanceRequestCommentCreateSerializer,
    AttendanceRequestCommentSerializer,
    AttendanceRequestSerializer,
    AttendanceSerializer,
    AttendanceValidationConditionSerializer,
    GraceTimeSerializer,
    MailTemplateSerializer,
)

# Create your views here.


def query_dict(data):
    query_dict = QueryDict("", mutable=True)
    for key, value in data.items():
        if isinstance(value, list):
            for item in value:
                query_dict.appendlist(key, item)
        else:
            query_dict.update({key: value})
    return query_dict


class ClockInAPIView(APIView):
    """
    Allows authenticated employees to clock in, determining the correct shift and attendance date, including handling night shifts.

    Methods:
        post(request): Processes and records the clock-in time.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("========", request.user.employee_get.check_online())
        if not request.user.employee_get.check_online():
            try:
                # Determine if WorkType is WFH-like; if so, skip geofence
                is_wfh = False
                try:
                    wt = request.user.employee_get.employee_work_info.work_type_id
                    wt_name = (wt.work_type or "").strip().lower() if wt else ""
                    is_wfh = wt_name in ["work from home", "wfh", "remote"]
                except Exception:
                    pass

                if (not is_wfh) and request.user.employee_get.get_company().geo_fencing.start:
                    from geofencing.views import GeoFencingEmployeeLocationCheckAPIView

                    location_api_view = GeoFencingEmployeeLocationCheckAPIView()
                    response = location_api_view.post(request)
                    if response.status_code != 200:
                        return response
            except:
                pass
            employee, work_info = employee_exists(request)
            datetime_now = datetime.now()
            if request._dict_.get("datetime"):
                datetime_now = request.datetime
            if employee and work_info is not None:
                shift = work_info.shift_id
                date_today = date.today()
                if request._dict_.get("date"):
                    date_today = request.date
                attendance_date = date_today
                day = date_today.strftime("%A").lower()
                day = EmployeeShiftDay.objects.get(day=day)
                now = datetime.now().strftime("%H:%M")
                if request._dict_.get("time"):
                    now = request.time.strftime("%H:%M")
                now_sec = strtime_seconds(now)
                mid_day_sec = strtime_seconds("12:00")
                minimum_hour, start_time_sec, end_time_sec = shift_schedule_today(
                    day=day, shift=shift
                )
                if start_time_sec > end_time_sec:
                    # night shift
                    # ------------------
                    # Night shift in Horilla consider a 24 hours from noon to next day noon,
                    # the shift day taken today if the attendance clocked in after 12 O clock.

                    if mid_day_sec > now_sec:
                        # Here you need to create attendance for yesterday

                        date_yesterday = date_today - timedelta(days=1)
                        day_yesterday = date_yesterday.strftime("%A").lower()
                        day_yesterday = EmployeeShiftDay.objects.get(day=day_yesterday)
                        minimum_hour, start_time_sec, end_time_sec = (
                            shift_schedule_today(day=day_yesterday, shift=shift)
                        )
                        attendance_date = date_yesterday
                        day = day_yesterday
                clock_in_attendance_and_activity(
                    employee=employee,
                    date_today=date_today,
                    attendance_date=attendance_date,
                    day=day,
                    now=now,
                    shift=shift,
                    minimum_hour=minimum_hour,
                    start_time=start_time_sec,
                    end_time=end_time_sec,
                    in_datetime=datetime_now,
                )
                return Response({"message": "Clocked-In"}, status=200)
            return Response(
                {
                    "error": "You Don't have work information filled or your employee detail neither entered "
                }
            )
        return Response({"message": "Already clocked-in"}, status=400)


class ClockOutAPIView(APIView):
    """
    Allows authenticated employees to clock out, updating the latest attendance record and handling early outs.

    Methods:
        post(request): Records the clock-out time.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:
            # Determine if WorkType is WFH-like; if so, skip geofence
            is_wfh = False
            try:
                wt = request.user.employee_get.employee_work_info.work_type_id
                wt_name = (wt.work_type or "").strip().lower() if wt else ""
                is_wfh = wt_name in ["work from home", "wfh", "remote"]
            except Exception:
                pass

            if (not is_wfh) and request.user.employee_get.get_company().geo_fencing.start:
                from geofencing.views import GeoFencingEmployeeLocationCheckAPIView

                location_api_view = GeoFencingEmployeeLocationCheckAPIView()
                response = location_api_view.post(request)
                if response.status_code != 200:
                    return response
        except:
            pass
        if request.user.employee_get.check_online():
            print("----------------")
            current_date = date.today()
            current_time = datetime.now().time()
            current_datetime = datetime.now()

            try:
                clock_out(
                    Request(
                        user=request.user,
                        date=current_date,
                        time=current_time,
                        datetime=current_datetime,
                    )
                )
                return Response({"message": "Clocked-Out"}, status=200)

            except Exception as error:
                logger.error("Got an error in clock_out", error)
            # return Response({"message": "Clocked-Out"}, status=200)
        return Response({"message": "Already clocked-out"}, status=400)


class AttendanceListPagination(PageNumberPagination):
    """Use page/vpage/opage per tab (validated / non-validated / ot) to match backend UI."""
    page_size = 15
    page_size_query_param = "page_size"

    def get_page_number(self, request):
        type_from_url = None
        if getattr(request, "resolver_match", None) and getattr(request.resolver_match, "kwargs", None):
            type_from_url = request.resolver_match.kwargs.get("type")
        param = "page"
        if type_from_url == "non-validated":
            param = "vpage"
        elif type_from_url == "ot":
            param = "opage"
        try:
            return int(request.query_params.get(param, 1))
        except (TypeError, ValueError):
            return 1


class AttendanceView(APIView):
    """
    Handles CRUD operations for attendance records.

    Methods:
        get_queryset(request, type): Returns filtered attendance records.
        get(request, pk=None, type=None): Retrieves a specific record or a list of records.
        post(request): Creates a new attendance record.
        put(request, pk): Updates an existing attendance record.
        delete(request, pk): Deletes an attendance record and adjusts related overtime if needed.
    """

    permission_classes = [IsAuthenticated]
    filterset_class = AttendanceFilters

    def get_queryset(self, request, type):
        # Align with backend attendance_view: only active employees (employee_id__is_active=True)
        base_filter = {"employee_id__is_active": True}
        if type == "ot":
            condition = AttendanceValidationCondition.objects.first()
            minot = strtime_seconds("00:30")
            if condition is not None:
                minot = strtime_seconds(condition.minimum_overtime_to_approve)
            queryset = Attendance.objects.filter(
                overtime_second__gte=minot,
                attendance_validated=True,
                **base_filter,
            )
        elif type == "validated":
            queryset = Attendance.objects.filter(
                attendance_validated=True, **base_filter
            )
        elif type == "non-validated":
            queryset = Attendance.objects.filter(
                attendance_validated=False, **base_filter
            )
        else:
            queryset = Attendance.objects.filter(**base_filter)
        user = request.user
        # checking user level permissions
        perm = "attendance.view_attendance"
        queryset = permission_based_queryset(user, perm, queryset, user_obj=True)
        return queryset

    def get(self, request, pk=None, type=None):
        # individual object workflow
        if pk:
            attendance = get_object_or_404(Attendance, pk=pk)
            serializer = AttendanceSerializer(instance=attendance)
            return Response(serializer.data, status=200)
        # permission based querysete
        attendances = self.get_queryset(request, type)
        # filtering queryset
        attendances_filter_queryset = self.filterset_class(
            request.GET, queryset=attendances
        ).qs
        sortby = request.GET.get("sortby", "").strip()
        if sortby:
            order_field = sortby.lstrip("-")
            valid_sort_fields = (
                "employee_id__employee_first_name",
                "batch_attendance_id__title",
                "attendance_date",
                "attendance_clock_in_date",
                "attendance_clock_out",
                "attendance_clock_out_date",
                "at_work_second",
                "overtime_second",
                "attendance_overtime",
            )
            if order_field in valid_sort_fields:
                attendances_filter_queryset = attendances_filter_queryset.order_by(
                    sortby
                )
        field_name = request.GET.get("groupby_field", None)
        if field_name:
            url = request.build_absolute_uri()
            return groupby_queryset(
                request, url, field_name, attendances_filter_queryset
            )
        # pagination workflow (page/vpage/opage per tab)
        paginater = AttendanceListPagination()
        page = paginater.paginate_queryset(attendances_filter_queryset, request)
        serializer = AttendanceSerializer(page, many=True)
        return paginater.get_paginated_response(serializer.data)

    @manager_permission_required("attendance.add_attendance")
    def post(self, request):
        serializer = AttendanceSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=200)
            except IntegrityError:
                return Response(
                    {
                        "error": [
                            "Attendance for this employee on this date already exists."
                        ]
                    },
                    status=400,
                )
        # Replace default unique-constraint message with a friendlier one
        serializer_errors = serializer.errors
        unique_error_msg = (
            "The fields employee_id, attendance_date must make a unique set."
        )
        if "non_field_errors" in serializer_errors and any(
            unique_error_msg in str(m) for m in serializer_errors["non_field_errors"]
        ):
            return Response(
                {
                    "error": [
                        "Attendance for this employee on this date already exists."
                    ]
                },
                status=400,
            )
        return Response(serializer_errors, status=400)

    @method_decorator(permission_required("attendance.change_attendance"))
    def put(self, request, pk):
        try:
            attendance = Attendance.objects.get(id=pk)
        except Attendance.DoesNotExist:
            return Response({"detail": "Attendance record not found."}, status=404)

        serializer = AttendanceSerializer(instance=attendance, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)

        # Customize error message for unique constraint
        serializer_errors = serializer.errors
        if "non_field_errors" in serializer.errors:
            unique_error_msg = (
                "The fields employee_id, attendance_date must make a unique set."
            )
            if unique_error_msg in serializer.errors["non_field_errors"]:
                serializer_errors = {
                    "non_field_errors": [
                        "The employee already has attendance on this date."
                    ]
                }
        return Response(serializer_errors, status=400)

    @method_decorator(permission_required("attendance.delete_attendance"))
    def delete(self, request, pk):
        attendance = Attendance.objects.get(id=pk)
        month = attendance.attendance_date
        month = month.strftime("%B").lower()
        overtime = attendance.employee_id.employee_overtime.filter(month=month).last()
        if overtime is not None:
            if attendance.attendance_overtime_approve:
                # Subtract overtime of this attendance
                total_overtime = strtime_seconds(overtime.overtime)
                attendance_overtime_seconds = strtime_seconds(
                    attendance.attendance_overtime
                )
                if total_overtime > attendance_overtime_seconds:
                    total_overtime = total_overtime - attendance_overtime_seconds
                else:
                    total_overtime = attendance_overtime_seconds - total_overtime
                overtime.overtime = format_time(total_overtime)
                overtime.save()
            try:
                attendance.delete()
                return Response({"status", "deleted"}, status=200)
            except Exception as error:
                return Response({"error:", f"{error}"}, status=400)
        else:
            try:
                attendance.delete()
                return Response({"status", "deleted"}, status=200)
            except Exception as error:
                return Response({"error:", f"{error}"}, status=400)


class AttendanceBulkValidateView(APIView):
    """
    Bulk validate attendance records.
    POST with body: { "ids": [1, 2, 3] }
    """

    permission_classes = [IsAuthenticated]

    @manager_permission_required("attendance.change_attendance")
    def post(self, request):
        from django.db import transaction
        from notifications.signals import notify
        from django.urls import reverse

        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"detail": "No attendances selected for validation."},
                status=400,
            )
        try:
            ids = [int(i) for i in ids]
        except (ValueError, TypeError):
            return Response({"detail": "Invalid list of IDs provided."}, status=400)

        validate_req_count = 0
        error_messages = []

        # Get attendances user can see (same permission as list)
        base_qs = Attendance.objects.filter(employee_id__is_active=True)
        permission_based = permission_based_queryset(
            request.user, "attendance.view_attendance", base_qs, user_obj=True
        )
        allowed_qs = permission_based.filter(id__in=ids)

        with transaction.atomic():
            for attendance in allowed_qs:
                try:
                    if attendance.is_validate_request:
                        error_messages.append(
                            f"Pending attendance update request for {attendance.employee_id}'s attendance on {attendance.attendance_date}!"
                        )
                        continue

                    attendance.attendance_validated = True
                    attendance.save()
                    validate_req_count += 1

                    # Send notification
                    try:
                        notify.send(
                            request.user.employee_get,
                            recipient=attendance.employee_id.employee_user_id,
                            verb=f"Your attendance for the date {attendance.attendance_date} is validated",
                            verb_ar=f"تم التحقق من حضورك في تاريخ {attendance.attendance_date}",
                            verb_de=f"Ihre Anwesenheit für das Datum {attendance.attendance_date} wurde bestätigt",
                            verb_es=f"Se ha validado su asistencia para la fecha {attendance.attendance_date}",
                            verb_fr=f"Votre présence pour la date {attendance.attendance_date} est validée",
                            redirect="/employee/employee-profile/",
                            api_redirect="",
                            icon="checkmark",
                        )
                    except Exception:
                        pass  # Notification failure shouldn't break validation

                except Exception as e:
                    error_messages.append(f"Error validating attendance {attendance.id}: {str(e)}")

        response_data = {
            "validated": validate_req_count,
            "errors": error_messages,
        }
        status_code = 200 if validate_req_count > 0 else 400
        return Response(response_data, status=status_code)


class AttendanceBulkDeleteView(APIView):
    """
    Bulk delete attendance records.
    POST with body: { "ids": [1, 2, 3] }
    """

    permission_classes = [IsAuthenticated]

    @manager_permission_required("attendance.delete_attendance")
    def post(self, request):
        from django.db import transaction
        from attendance.methods.utils import strtime_seconds, format_time

        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"detail": "No attendances selected for deletion."},
                status=400,
            )
        try:
            ids = [int(i) for i in ids]
        except (ValueError, TypeError):
            return Response({"detail": "Invalid list of IDs provided."}, status=400)

        success_count = 0
        error_messages = []

        # Get attendances user can see (same permission as list)
        base_qs = Attendance.objects.filter(employee_id__is_active=True)
        permission_based = permission_based_queryset(
            request.user, "attendance.view_attendance", base_qs, user_obj=True
        )
        deletable_qs = permission_based.filter(id__in=ids)

        employee_ids = deletable_qs.values_list("employee_id", flat=True)
        overtimes = AttendanceOverTime.objects.filter(
            employee_id__in=employee_ids
        ).in_bulk()

        with transaction.atomic():
            for attendance in deletable_qs:
                try:
                    month = attendance.attendance_date.strftime("%B").lower()
                    overtime = overtimes.get(attendance.employee_id.id)

                    if overtime and attendance.attendance_overtime_approve:
                        # Calculate the new overtime
                        total_overtime = strtime_seconds(overtime.overtime)
                        attendance_overtime_seconds = strtime_seconds(
                            attendance.attendance_overtime
                        )
                        total_overtime = abs(total_overtime - attendance_overtime_seconds)
                        overtime.overtime = format_time(total_overtime)
                        overtime.save()

                    attendance.delete()
                    success_count += 1

                except Exception as e:
                    error_messages.append(f"Error deleting attendance {attendance.id}: {str(e)}")

        response_data = {
            "deleted": success_count,
            "errors": error_messages,
        }
        status_code = 200 if success_count > 0 else 400
        return Response(response_data, status=status_code)


class ValidateAttendanceView(APIView):
    """
    Validates an attendance record and sends a notification to the employee.

    Method:
        put(request, pk): Marks the attendance as validated and notifies the employee.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        attendance = Attendance.objects.filter(id=pk).update(attendance_validated=True)
        attendance = Attendance.objects.filter(id=pk).first()
        try:
            notify.send(
                request.user.employee_get,
                recipient=attendance.employee_id.employee_user_id,
                verb=f"Your attendance for the date {attendance.attendance_date} is validated",
                verb_ar=f"تم تحقيق حضورك في تاريخ {attendance.attendance_date}",
                verb_de=f"Deine Anwesenheit für das Datum {attendance.attendance_date} ist bestätigt.",
                verb_es=f"Se valida tu asistencia para la fecha {attendance.attendance_date}.",
                verb_fr=f"Votre présence pour la date {attendance.attendance_date} est validée.",
                redirect="/attendance/view-my-attendance",
                icon="checkmark",
                api_redirect=f"/api/attendance/attendance?employee_id{attendance.employee_id}",
            )
        except:
            pass
        return Response(status=200)


class OvertimeApproveView(APIView):
    """
    Approves overtime for an attendance record and sends a notification to the employee.

    Method:
        put(request, pk): Marks the overtime as approved and notifies the employee.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            attendance = Attendance.objects.filter(id=pk).update(
                attendance_overtime_approve=True
            )
        except Exception as E:
            return Response({"error": str(E)}, status=400)

        attendance = Attendance.objects.filter(id=pk).first()
        try:
            notify.send(
                request.user.employee_get,
                recipient=attendance.employee_id.employee_user_id,
                verb=f"Your {attendance.attendance_date}'s attendance overtime approved.",
                verb_ar=f"تمت الموافقة على إضافة ساعات العمل الإضافية لتاريخ {attendance.attendance_date}.",
                verb_de=f"Die Überstunden für den {attendance.attendance_date} wurden genehmigt.",
                verb_es=f"Se ha aprobado el tiempo extra de asistencia para el {attendance.attendance_date}.",
                verb_fr=f"Les heures supplémentaires pour la date {attendance.attendance_date} ont été approuvées.",
                redirect="/attendance/attendance-overtime-view",
                icon="checkmark",
                api_redirect="/api/attendance/attendance-hour-account/",
            )
        except:
            pass
        return Response(status=200)


class AttendanceRequestView(APIView):
    """
    Handles requests for creating, updating, and viewing attendance records.

    Methods:
        get(request, pk=None): Retrieves a specific attendance request by pk or a filtered list of requests.
        post(request): Creates a new attendance request.
        put(request, pk): Updates an existing attendance request.
    """

    serializer_class = AttendanceRequestSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            attendance = Attendance.objects.get(id=pk)
            serializer = AttendanceRequestSerializer(instance=attendance)
            return Response(serializer.data, status=200)

        requests = Attendance.objects.filter(
            is_validate_request=True,
        )
        requests = filtersubordinates(
            request=request,
            perm="attendance.view_attendance",
            queryset=requests,
        )
        requests = requests | Attendance.objects.filter(
            employee_id__employee_user_id=request.user,
            is_validate_request=True,
        )
        request_filtered_queryset = AttendanceFilters(request.GET, requests).qs
        sortby = request.GET.get("sortby", "").strip()
        if sortby:
            order_field = sortby
            if order_field.startswith("-"):
                order_field = order_field[1:]
            valid_sort_fields = (
                "employee_id__employee_first_name",
                "batch_attendance_id__title",
                "attendance_date",
                "attendance_clock_in_date",
                "attendance_clock_out_date",
                "attendance_overtime",
            )
            if order_field in valid_sort_fields:
                request_filtered_queryset = request_filtered_queryset.order_by(
                    sortby
                )
        field_name = request.GET.get("groupby_field", None)
        if field_name:
            # groupby workflow
            url = request.build_absolute_uri()
            return groupby_queryset(request, url, field_name, request_filtered_queryset)

        pagenation = PageNumberPagination()
        page = pagenation.paginate_queryset(request_filtered_queryset, request)
        serializer = self.serializer_class(page, many=True)
        return pagenation.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = AttendanceRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        employee_id = request.data.get("employee_id")
        attendance_date = request.data.get("attendance_date", date.today())
        if Attendance.objects.filter(
            employee_id=employee_id, attendance_date=attendance_date
        ).exists():
            return Response(
                {
                    "error": [
                        "Attendance for this employee on the current date already exists."
                    ]
                },
                status=400,
            )
        return Response(serializer.errors, status=404)

    @manager_permission_required("attendance.update_attendance")
    def put(self, request, pk):
        attendance = Attendance.objects.get(id=pk)
        serializer = AttendanceRequestSerializer(instance=attendance, data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            instance.employee_id = attendance.employee_id
            instance.id = attendance.id
            if attendance.request_type != "create_request":
                attendance.requested_data = json.dumps(instance.serialize())
                attendance.request_description = instance.request_description
                attendance.is_validate_request = True
                attendance.save()
            else:
                instance.is_validate_request_approved = False
                instance.is_validate_request = True
                instance.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=404)


class AttendanceRequestBulkCreateAPIView(APIView):
    """
    Create attendance requests for a date range (bulk).
    POST body: employee_id, from_date, to_date, shift_id, work_type_id,
    attendance_clock_in, attendance_clock_out, attendance_worked_hour, minimum_hour,
    request_description, batch_attendance_id (optional).
    """

    permission_classes = [IsAuthenticated]

    @manager_permission_required("attendance.update_attendance")
    def post(self, request):
        from attendance.forms import get_date_list
        from employee.models import Employee

        employee_id = request.data.get("employee_id")
        from_date = request.data.get("from_date")
        to_date = request.data.get("to_date")
        if not employee_id or not from_date or not to_date:
            return Response(
                {"error": "employee_id, from_date, and to_date are required"},
                status=400,
            )
        try:
            from_date = datetime.strptime(str(from_date), "%Y-%m-%d").date()
            to_date = datetime.strptime(str(to_date), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return Response({"error": "Invalid date format (use YYYY-MM-DD)"}, status=400)
        if from_date > to_date:
            return Response({"error": "from_date must be before or equal to to_date"}, status=400)
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=404)
        date_list = get_date_list(employee, from_date, to_date)
        if not date_list:
            return Response(
                {"error": "No valid dates in range (may have existing attendance or approved leave)"},
                status=400,
            )
        shift_id = request.data.get("shift_id")
        work_type_id = request.data.get("work_type_id") or (
            getattr(employee.employee_work_info, "work_type_id_id", None)
            if getattr(employee, "employee_work_info", None)
            else None
        )
        request_description = (request.data.get("request_description") or "").strip()
        if not request_description:
            return Response({"error": "request_description is required"}, status=400)
        attendance_clock_in = request.data.get("attendance_clock_in")
        attendance_clock_out = request.data.get("attendance_clock_out")
        attendance_worked_hour = request.data.get("attendance_worked_hour") or "00:00"
        minimum_hour = request.data.get("minimum_hour") or "00:00"
        batch_attendance_id = request.data.get("batch_attendance_id")
        created = []
        for d in date_list:
            data = {
                "employee_id": employee_id,
                "attendance_date": str(d),
                "attendance_clock_in_date": str(d),
                "attendance_clock_out_date": str(d),
                "attendance_clock_in": attendance_clock_in,
                "attendance_clock_out": attendance_clock_out,
                "attendance_worked_hour": attendance_worked_hour,
                "minimum_hour": minimum_hour,
                "request_description": request_description,
                "is_bulk_request": True,
            }
            if shift_id:
                data["shift_id"] = int(shift_id)
            if work_type_id:
                data["work_type_id"] = int(work_type_id)
            if batch_attendance_id:
                data["batch_attendance_id"] = int(batch_attendance_id)
            serializer = AttendanceRequestSerializer(data=data)
            if serializer.is_valid():
                inst = serializer.save()
                inst.is_bulk_request = True
                inst.save(update_fields=["is_bulk_request"])
                created.append(inst.id)
        return Response({"created": len(created), "ids": created}, status=201)


class AttendanceRequestIdsView(APIView):
    """
    Returns IDs of all attendance requests matching the current filters.
    Used for "Select All Records" across pages.
    GET with same params as attendance-request list (filters, search, etc.)
    Returns: { ids: [1, 2, 3, ...] }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests_qs = Attendance.objects.filter(is_validate_request=True)
        requests_qs = filtersubordinates(
            request=request,
            perm="attendance.view_attendance",
            queryset=requests_qs,
        )
        requests_qs = requests_qs | Attendance.objects.filter(
            employee_id__employee_user_id=request.user,
            is_validate_request=True,
        )
        filtered = AttendanceFilters(request.GET, requests_qs).qs
        ids = list(filtered.values_list("id", flat=True))
        return Response({"ids": ids})


class AttendanceHourAccountIdsView(APIView):
    """
    Returns IDs of all hour account records matching the current filters.
    Used for "Select All Records" across pages.
    GET with same params as attendance-hour-account list.
    Returns: { ids: [1, 2, 3, ...] }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        filterset = AttendanceOverTimeFilter(request.GET)
        queryset = filterset.qs
        self_account = queryset.filter(employee_id__employee_user_id=request.user)
        permission_based = filtersubordinates(
            request, queryset, "attendance.view_attendanceovertime"
        )
        queryset = (permission_based | self_account).distinct()
        ids = list(queryset.values_list("id", flat=True))
        return Response({"ids": ids})


class AttendanceRequestValidateDetailView(APIView):
    """
    Returns validate modal data: employee info, current vs requested diff, prev/next ids.
    GET /api/v1/attendance/attendance-request-validate-detail/<pk>/?requests_ids=1,2,3
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            attendance = Attendance.objects.get(id=pk)
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance request not found"}, status=404)

        requests_qs = Attendance.objects.filter(is_validate_request=True)
        requests_qs = filtersubordinates(
            request=request,
            perm="attendance.view_attendance",
            queryset=requests_qs,
        )
        requests_qs = requests_qs | Attendance.objects.filter(
            employee_id__employee_user_id=request.user,
            is_validate_request=True,
        )
        if not requests_qs.filter(id=pk).exists():
            return Response({"error": "Access denied"}, status=403)

        first_dict = attendance.serialize()
        empty_data = {
            "employee_id": None,
            "attendance_date": None,
            "attendance_clock_in_date": None,
            "attendance_clock_in": None,
            "attendance_clock_out": None,
            "attendance_clock_out_date": None,
            "shift_id": None,
            "work_type_id": None,
            "attendance_worked_hour": None,
            "batch_attendance_id": None,
        }
        if attendance.request_type == "create_request":
            other_dict = first_dict
            first_dict = empty_data
        else:
            other_dict = json.loads(attendance.requested_data) if attendance.requested_data else {}

        diff_raw = get_diff_dict(first_dict, other_dict, Attendance)
        diff = {}
        for key, pair in diff_raw.items():
            v1, v2 = pair
            diff[key] = [str(v1) if v1 is not None else "", str(v2) if v2 is not None else ""]

        emp = attendance.employee_id
        department = ""
        job_position = ""
        try:
            wi = getattr(emp, "employee_work_info", None)
            if wi:
                department = str(wi.department_id) if wi.department_id else ""
                job_position = str(wi.job_position_id) if wi.job_position_id else ""
        except Exception:
            pass

        previous_id = next_id = pk
        requests_ids_json = request.GET.get("requests_ids")
        if requests_ids_json:
            try:
                ids = [int(x) for x in requests_ids_json.split(",") if x.strip()]
                previous_id, next_id = closest_numbers(ids, int(pk))
            except (ValueError, TypeError):
                pass

        form_initial = dict(other_dict) if other_dict else {}
        form_initial["request_description"] = attendance.request_description or ""
        form_initial["employee_id"] = emp.id

        return Response({
            "id": attendance.id,
            "employee_id": emp.id,
            "employee_name": emp.get_full_name() or "",
            "employee_profile_url": emp.get_avatar() if hasattr(emp, "get_avatar") else None,
            "department": department,
            "job_position": job_position,
            "diff": diff,
            "request_description": attendance.request_description or "",
            "form_initial": form_initial,
            "previous_id": previous_id,
            "next_id": next_id,
        }, status=200)


def _can_access_attendance_request(request, attendance):
    """Check if user can access an attendance request (view/add comment)."""
    requests_qs = Attendance.objects.filter(id=attendance.id)
    requests_qs = filtersubordinates(
        request=request,
        perm="attendance.view_attendance",
        queryset=requests_qs,
    )
    requests_qs = requests_qs | Attendance.objects.filter(
        id=attendance.id,
        employee_id__employee_user_id=request.user,
    )
    return requests_qs.exists()


class AttendanceRequestCommentsAPIView(APIView):
    """
    List and add comments for an attendance request.
    GET: list comments
    POST: add comment (body: { comment: "..." })
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            attendance = Attendance.objects.get(id=pk)
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance request not found"}, status=404)
        if not _can_access_attendance_request(request, attendance):
            return Response({"error": "Access denied"}, status=403)
        comments = (
            AttendanceRequestComment.objects.filter(request_id=pk)
            .order_by("-created_at")
        )
        return Response(
            {"results": AttendanceRequestCommentSerializer(comments, many=True).data},
            status=200,
        )

    def post(self, request, pk):
        try:
            attendance = Attendance.objects.get(id=pk)
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance request not found"}, status=404)
        if not _can_access_attendance_request(request, attendance):
            return Response({"error": "Access denied"}, status=403)
        emp = getattr(request.user, "employee_get", None)
        if not emp:
            return Response({"error": "Employee profile required"}, status=400)
        serializer = AttendanceRequestCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = AttendanceRequestComment()
        comment.request_id = attendance
        comment.employee_id = emp
        comment.comment = serializer.validated_data.get("comment", "").strip()
        comment.save()
        return Response(
            AttendanceRequestCommentSerializer(comment).data,
            status=201,
        )


class AttendanceRequestCommentDeleteAPIView(APIView):
    """Delete an attendance request comment."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, comment_id):
        try:
            comment = AttendanceRequestComment.objects.get(
                id=comment_id,
                request_id=pk,
            )
        except AttendanceRequestComment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=404)
        attendance = comment.request_id
        if not _can_access_attendance_request(request, attendance):
            return Response({"error": "Access denied"}, status=403)
        emp = getattr(request.user, "employee_get", None)
        if emp and comment.employee_id_id == emp.id:
            pass
        elif request.user.has_perm("attendance.delete_attendancerequestcomment"):
            pass
        else:
            return Response({"error": "Cannot delete this comment"}, status=403)
        comment.delete()
        return Response(status=204)


class AttendanceRequestApproveView(APIView):
    """
    Approves and updates an attendance request.

    Method:
        put(request, pk): Approves the attendance request, updates attendance records, and handles related activities.
    """

    permission_classes = [IsAuthenticated]

    @manager_permission_required("attendance.change_attendance")
    def put(self, request, pk):
        try:
            attendance = Attendance.objects.get(id=pk)
            prev_attendance_date = attendance.attendance_date
            prev_attendance_clock_in_date = attendance.attendance_clock_in_date
            prev_attendance_clock_in = attendance.attendance_clock_in
            attendance.attendance_validated = True
            attendance.is_validate_request_approved = True
            attendance.is_validate_request = False
            attendance.request_description = None
            attendance.save()
            if attendance.requested_data is not None:
                requested_data = json.loads(attendance.requested_data)
                requested_data["attendance_clock_out"] = (
                    None
                    if requested_data["attendance_clock_out"] == "None"
                    else requested_data["attendance_clock_out"]
                )
                requested_data["attendance_clock_out_date"] = (
                    None
                    if requested_data["attendance_clock_out_date"] == "None"
                    else requested_data["attendance_clock_out_date"]
                )
                Attendance.objects.filter(id=pk).update(**requested_data)
                # DUE TO AFFECT THE OVERTIME CALCULATION ON SAVE METHOD, SAVE THE INSTANCE ONCE MORE
                attendance = Attendance.objects.get(id=pk)
                attendance.save()
            if (
                attendance.attendance_clock_out is None
                or attendance.attendance_clock_out_date is None
            ):
                attendance.attendance_validated = True
                activity = AttendanceActivity.objects.filter(
                    employee_id=attendance.employee_id,
                    attendance_date=prev_attendance_date,
                    clock_in_date=prev_attendance_clock_in_date,
                    clock_in=prev_attendance_clock_in,
                )
                if activity:
                    activity.update(
                        employee_id=attendance.employee_id,
                        attendance_date=attendance.attendance_date,
                        clock_in_date=attendance.attendance_clock_in_date,
                        clock_in=attendance.attendance_clock_in,
                    )

                else:
                    AttendanceActivity.objects.create(
                        employee_id=attendance.employee_id,
                        attendance_date=attendance.attendance_date,
                        clock_in_date=attendance.attendance_clock_in_date,
                        clock_in=attendance.attendance_clock_in,
                    )
        except Exception as E:
            return Response({"error": str(E)}, status=400)
        return Response({"status": "approved"}, status=200)


class AttendanceRequestCancelView(APIView):
    """
    Cancels an attendance request.

    Method:
        put(request, pk): Cancels the attendance request, resetting its status and data, and deletes the request if it was a create request.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            attendance = Attendance.objects.get(id=pk)
            if (
                attendance.employee_id.employee_user_id == request.user
                or is_reportingmanager(request)
                or request.user.has_perm("attendance.change_attendance")
            ):
                attendance.is_validate_request_approved = False
                attendance.is_validate_request = False
                attendance.request_description = None
                attendance.requested_data = None
                attendance.request_type = None

                attendance.save()
                if attendance.request_type == "create_request":
                    attendance.delete()
        except Exception as E:
            return Response({"error": str(E)}, status=400)
        return Response({"status": "success"}, status=200)


class BatchListAPIView(APIView):
    """
    Lists attendance batches for dropdowns and batch management.

    Method:
        get(request): Returns list of batches (id, title).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        batches = BatchAttendance.objects.all().order_by("-id")
        data = [{"id": b.id, "title": str(b.title) if b.title else f"Batch-{b.id}"} for b in batches]
        return Response(data, status=200)

    @manager_permission_required("attendance.add_batchattendance")
    def post(self, request):
        title = (request.data.get("title") or "").strip()
        if not title:
            return Response({"error": "title is required"}, status=400)
        batch = BatchAttendance.objects.create(title=title)
        return Response({"id": batch.id, "title": str(batch.title)}, status=201)


class BatchDetailAPIView(APIView):
    """Update or delete a batch. PUT: update title. DELETE: delete batch."""

    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        batch = BatchAttendance.objects.filter(id=pk).first()
        if not batch:
            return Response({"error": "Batch not found"}, status=404)
        if not (
            request.user.has_perm("attendance.change_attendancegeneralsettings")
            or getattr(batch, "created_by_id", None) == getattr(request.user, "id", None)
        ):
            return Response({"error": "Permission denied"}, status=403)
        title = (request.data.get("title") or "").strip()
        if not title:
            return Response({"error": "title is required"}, status=400)
        batch.title = title
        batch.save()
        return Response({"id": batch.id, "title": str(batch.title)}, status=200)

    @method_decorator(permission_required("attendance.delete_batchattendance"))
    def delete(self, request, pk):
        from django.db.models import ProtectedError

        batch = BatchAttendance.objects.filter(id=pk).first()
        if not batch:
            return Response({"error": "Batch not found"}, status=404)
        try:
            batch_name = str(batch)
            batch.delete()
            return Response({"status": "deleted", "batch": batch_name}, status=200)
        except ProtectedError as e:
            return Response(
                {"error": f"Batch is in use and cannot be deleted: {e}"},
                status=400,
            )


class AttendanceRequestAddToBatchAPIView(APIView):
    """
    Adds selected attendance request IDs to a batch.

    Method:
        post(request): Body { ids: [1, 2, 3], batch_attendance_id: 1 }.
    """

    permission_classes = [IsAuthenticated]

    @manager_permission_required("attendance.change_attendance")
    def post(self, request):
        ids = request.data.get("ids")
        batch_id = request.data.get("batch_attendance_id")
        if not ids or not isinstance(ids, list):
            return Response({"error": "ids must be a non-empty list"}, status=400)
        if not batch_id:
            return Response({"error": "batch_attendance_id is required"}, status=400)
        batch = BatchAttendance.objects.filter(id=batch_id).first()
        if not batch:
            return Response({"error": "Batch not found"}, status=404)
        updated = 0
        for pk in ids:
            try:
                att = Attendance.objects.filter(id=pk).first()
                if att:
                    att.batch_attendance_id = batch
                    att.save()
                    updated += 1
            except Exception:
                pass
        return Response({"status": "success", "updated": updated, "batch": str(batch)}, status=200)


class AttendanceOverTimeView(APIView):
    """
    Manages CRUD operations for attendance overtime records.

    Methods:
        get(request, pk=None): Retrieves a specific overtime record by pk or a list of records with filtering and pagination.
        post(request): Creates a new overtime record.
        put(request, pk): Updates an existing overtime record.
        delete(request, pk): Deletes an overtime record.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            attendance_ot = get_object_or_404(AttendanceOverTime, pk=pk)
            serializer = AttendanceOverTimeSerializer(attendance_ot)
            return Response(serializer.data, status=200)

        filterset_class = AttendanceOverTimeFilter(request.GET)
        queryset = filterset_class.qs
        self_account = queryset.filter(employee_id__employee_user_id=request.user)
        permission_based_queryset = filtersubordinates(
            request, queryset, "attendance.view_attendanceovertime"
        )
        queryset = (permission_based_queryset | self_account).distinct()
        field_name = request.GET.get("groupby_field", None)
        if field_name:
            # groupby workflow
            url = request.build_absolute_uri()
            return groupby_queryset(request, url, field_name, queryset)

        sortby = request.GET.get("sortby", "").strip()
        valid_sort_fields = (
            "employee_id__employee_first_name",
            "month",
            "year",
            "hour_account_second",
            "overtime_second",
        )
        if sortby:
            order_field = sortby.lstrip("-")
            if order_field in valid_sort_fields:
                queryset = queryset.order_by(sortby)

        pagenation = PageNumberPagination()
        page = pagenation.paginate_queryset(queryset, request)
        serializer = AttendanceOverTimeSerializer(page, many=True)
        return pagenation.get_paginated_response(serializer.data)

    @manager_permission_required("attendance.add_attendanceovertime")
    def post(self, request):
        serializer = AttendanceOverTimeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @manager_permission_required("attendance.change_attendanceovertime")
    def put(self, request, pk):
        attendance_ot = get_object_or_404(AttendanceOverTime, pk=pk)
        serializer = AttendanceOverTimeSerializer(
            instance=attendance_ot, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("attendance.delete_attendanceovertime"))
    def delete(self, request, pk):
        attendance = get_object_or_404(AttendanceOverTime, pk=pk)
        attendance.delete()

        return Response({"message": "Overtime deleted successfully"}, status=204)


class LateComeEarlyOutView(APIView):
    """
    Handles retrieval and deletion of late come and early out records.

    Methods:
        get(request): List with pagination and filters (search, type, attendance_date__gte/lte, etc.).
        delete(request, pk): Deletes a specific late come or early out record by pk.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            obj = get_object_or_404(AttendanceLateComeEarlyOut, pk=pk)
            serializer = AttendanceLateComeEarlyOutSerializer(obj)
            return Response(serializer.data, status=200)
        base_qs = AttendanceLateComeEarlyOut.objects.all().select_related(
            "attendance_id", "employee_id"
        )
        filter_obj = LateComeEarlyOutFilter(request.GET, queryset=base_qs)
        queryset = filter_obj.qs
        self_reports = queryset.filter(employee_id__employee_user_id=request.user)
        permission_based = filtersubordinates(
            request, filter_obj.qs, "attendance.view_attendancelatecomeearlyout", field="employee_id"
        )
        queryset = (permission_based | self_reports).distinct()
        sortby = request.GET.get("sortby", "").strip()
        valid_sort_fields = (
            "employee_id__employee_first_name",
            "type",
            "attendance_id__attendance_date",
            "attendance_id__attendance_clock_in_date",
            "attendance_id__attendance_clock_out_date",
            "attendance_id__at_work_second",
        )
        if sortby:
            order_field = sortby.lstrip("-")
            if order_field in valid_sort_fields:
                queryset = queryset.order_by(sortby)
            else:
                queryset = queryset.order_by("-attendance_id__attendance_date")
        else:
            queryset = queryset.order_by("-attendance_id__attendance_date")
        field_name = request.GET.get("groupby_field", None)
        if field_name:
            url = request.build_absolute_uri()
            return groupby_queryset(request, url, field_name, queryset)
        pagination = PageNumberPagination()
        pagination.page_size = request.GET.get("page_size") or pagination.page_size
        page = pagination.paginate_queryset(queryset, request)
        serializer = AttendanceLateComeEarlyOutSerializer(page, many=True)
        return pagination.get_paginated_response(serializer.data)

    def delete(self, request, pk=None):
        if not pk:
            return Response({"detail": "Not found."}, status=404)
        obj = get_object_or_404(AttendanceLateComeEarlyOut, pk=pk)
        obj.delete()
        return Response(status=204)


class LateComeEarlyOutExportAPIView(APIView):
    """
    Export late come / early out records to Excel. Uses same filters as list view.
    GET with same params as late-come-early-out-view/ (search, type, employee_id, etc.)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.http import HttpResponse

        base_qs = AttendanceLateComeEarlyOut.objects.all().select_related(
            "attendance_id", "employee_id"
        )
        filter_obj = LateComeEarlyOutFilter(request.GET, queryset=base_qs)
        queryset = filter_obj.qs
        self_reports = queryset.filter(employee_id__employee_user_id=request.user)
        permission_based = filtersubordinates(
            request, filter_obj.qs, "attendance.view_attendancelatecomeearlyout", field="employee_id"
        )
        queryset = (permission_based | self_reports).distinct().order_by(
            "-attendance_id__attendance_date"
        )

        from attendance.methods.utils import format_time as format_time_sec

        rows = []
        for obj in queryset:
            att = obj.attendance_id
            emp = obj.employee_id
            emp_name = ""
            if emp:
                f = getattr(emp, "employee_first_name", "") or getattr(emp, "first_name", "")
                l = getattr(emp, "employee_last_name", "") or getattr(emp, "last_name", "")
                emp_name = f"{f} {l}".strip() or str(emp)
            type_label = "Late Come" if obj.type == "late_come" else "Early Out"
            rows.append({
                "Employee": emp_name,
                "Type": type_label,
                "Attendance Date": att.attendance_date.strftime("%Y-%m-%d") if att and att.attendance_date else "",
                "Check-In Date": att.attendance_clock_in_date.strftime("%Y-%m-%d") if att and att.attendance_clock_in_date else "",
                "Check-In": att.attendance_clock_in.strftime("%H:%M") if att and att.attendance_clock_in else "",
                "Check-Out Date": att.attendance_clock_out_date.strftime("%Y-%m-%d") if att and att.attendance_clock_out_date else "",
                "Check-Out": att.attendance_clock_out.strftime("%H:%M") if att and att.attendance_clock_out else "",
                "Minimum Hour": str(att.minimum_hour) if att and att.minimum_hour else "",
                "At Work": format_time_sec(att.at_work_second) if att and getattr(att, "at_work_second", None) is not None else "",
            })

        df = pd.DataFrame(rows)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1")
            worksheet = writer.sheets["Sheet1"]
            for col_idx, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).map(len).max() if len(df) > 0 else 0, len(col))
                worksheet.set_column(col_idx, col_idx, min(max_len + 1, 50))

        output.seek(0)
        today_str = date.today().strftime("%Y-%m-%d")
        filename = f"Late_come_early_out_{today_str}.xlsx"
        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ValidationConditionAPIView(APIView):
    """
    GET: Return the single AttendanceValidationCondition instance (or 404).
    POST: Create the condition (only when none exists).
    PUT: Update the condition by id.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            condition = get_object_or_404(AttendanceValidationCondition, pk=pk)
        else:
            condition = AttendanceValidationCondition.objects.first()
            if not condition:
                return Response({"detail": "Not found."}, status=404)
        serializer = AttendanceValidationConditionSerializer(condition)
        return Response(serializer.data, status=200)

    @method_decorator(permission_required("attendance.add_attendancevalidationcondition"))
    def post(self, request):
        serializer = AttendanceValidationConditionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=201)
            except DjangoValidationError as e:
                detail = e.messages[0] if e.messages else str(e)
                return Response({"detail": detail}, status=400)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("attendance.change_attendancevalidationcondition"))
    def put(self, request, pk):
        condition = get_object_or_404(AttendanceValidationCondition, pk=pk)
        serializer = AttendanceValidationConditionSerializer(
            instance=condition, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


class AttendanceGeneralSettingAPIView(APIView):
    """
    GET: List all AttendanceGeneralSetting instances (one per company).
    PATCH: Update enable_check_in for a specific setting.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings = AttendanceGeneralSetting.objects.all()
        serializer = AttendanceGeneralSettingSerializer(settings, many=True)
        return Response(serializer.data, status=200)

    @method_decorator(permission_required("attendance.change_attendancegeneralsetting"))
    def patch(self, request, pk):
        setting = get_object_or_404(AttendanceGeneralSetting, pk=pk)
        serializer = AttendanceGeneralSettingSerializer(
            instance=setting, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


class GraceTimeAPIView(APIView):
    """
    CRUD API for GraceTime settings.

    GET /grace-time/           -> list all grace times (default and non-default)
    GET /grace-time/<id>/      -> retrieve a single grace time
    POST /grace-time/          -> create a grace time
    PATCH /grace-time/<id>/    -> partial update (e.g. toggles, allowed_time)
    DELETE /grace-time/<id>/   -> delete a grace time
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            instance = get_object_or_404(GraceTime, pk=pk)
            serializer = GraceTimeSerializer(instance)
            return Response(serializer.data, status=200)
        queryset = GraceTime.objects.all().order_by("-is_default", "allowed_time")
        serializer = GraceTimeSerializer(queryset, many=True)
        return Response(serializer.data, status=200)

    @method_decorator(permission_required("attendance.add_gracetime"))
    def post(self, request):
        serializer = GraceTimeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                instance = serializer.save()
                return Response(GraceTimeSerializer(instance).data, status=201)
            except DjangoValidationError as e:
                detail = e.messages[0] if getattr(e, "messages", None) else str(e)
                return Response({"detail": detail}, status=400)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("attendance.change_gracetime"))
    def patch(self, request, pk):
        instance = get_object_or_404(GraceTime, pk=pk)
        serializer = GraceTimeSerializer(instance=instance, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                instance = serializer.save()
                return Response(GraceTimeSerializer(instance).data, status=200)
            except DjangoValidationError as e:
                detail = e.messages[0] if getattr(e, "messages", None) else str(e)
                return Response({"detail": detail}, status=400)
        return Response(serializer.errors, status=400)

    @method_decorator(permission_required("attendance.delete_gracetime"))
    def delete(self, request, pk):
        instance = get_object_or_404(GraceTime, pk=pk)
        instance.delete()
        return Response(status=204)


class AttendanceActivityView(APIView):
    """
    Retrieves attendance activity records with filtering, permission-based visibility, and pagination.

    Method:
        get(request): List with params: page, page_size, search, attendance_date_from,
                      attendance_date_till, employee_id, etc. (AttendanceActivityFilter).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        filter_obj = AttendanceActivityFilter(request.GET, queryset=AttendanceActivity.objects.all())
        queryset = filter_obj.qs
        self_activities = queryset.filter(employee_id__employee_user_id=request.user)
        permission_based = filtersubordinates(
            request, filter_obj.qs, "attendance.view_attendanceovertime", field="employee_id"
        )
        queryset = (permission_based | self_activities).distinct()
        orderby = request.GET.get("orderby", "").strip()
        if orderby:
            order_field = orderby.lstrip("-")
            valid_order_fields = {
                "employee_id__employee_first_name",
                "attendance_date",
                "clock_in_date",
                "clock_out_date",
            }
            if order_field in valid_order_fields:
                queryset = queryset.order_by(orderby)
            else:
                queryset = queryset.order_by("-pk")
        else:
            queryset = queryset.order_by("-pk")
        field_name = request.GET.get("groupby_field", None)
        if field_name:
            url = request.build_absolute_uri()
            return groupby_queryset(request, url, field_name, queryset)
        pagination = PageNumberPagination()
        pagination.page_size = request.GET.get("page_size") or pagination.page_size
        page = pagination.paginate_queryset(queryset, request)
        serializer = AttendanceActivitySerializer(page, many=True)
        return pagination.get_paginated_response(serializer.data)


class AttendanceActivityBulkDeleteView(APIView):
    """
    Bulk delete attendance activity records.
    POST with body: { "ids": [1, 2, 3] }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from django.db import transaction
        ids = request.data.get("ids") if isinstance(request.data, dict) else []
        if not ids:
            return Response(
                {"detail": "No attendance activities selected for deletion."},
                status=400,
            )
        try:
            ids = [int(i) for i in ids]
        except (ValueError, TypeError):
            return Response({"detail": "Invalid list of IDs provided."}, status=400)
        # Restrict to activities user can see (same permission as list)
        base_qs = AttendanceActivity.objects.all()
        self_activities = base_qs.filter(employee_id__employee_user_id=request.user)
        permission_based = filtersubordinates(
            request, base_qs, "attendance.view_attendanceovertime", field="employee_id"
        )
        allowed_qs = (permission_based | self_activities).distinct()
        deletable = AttendanceActivity.objects.filter(id__in=ids).filter(
            id__in=allowed_qs.values_list("id", flat=True)
        )
        if not request.user.has_perm("attendance.delete_attendanceactivity"):
            return Response({"detail": "Permission denied."}, status=403)
        with transaction.atomic():
            count = deletable.count()
            deletable.delete()
        return Response({"deleted": count}, status=200)


class AttendanceActivityExportColumnsAPIView(APIView):
    """
    Returns available Excel columns for attendance activity export.
    GET /api/v1/attendance/attendance-activity-export-columns/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        form = AttendanceActivityExportForm()
        choices = form.fields["selected_fields"].choices
        columns = [{"value": value, "label": str(label)} for value, label in choices]
        return Response({"columns": columns}, status=200)


class AttendanceActivityExportAPIView(APIView):
    """
    Export attendance activities to Excel.
    GET with params: selected_fields (repeated), ids (optional JSON array for selected-only),
    and any AttendanceActivityFilter params (employee_id, attendance_date_from, etc.).
    Uses Django export_data logic when ids provided without selected_fields.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        django_request = request._request
        # Ensure we bypass HX form render and go to export_data
        django_request.META["HTTP_HX_REQUEST"] = "false"
        from attendance.views.views import attendance_activity_export

        response = attendance_activity_export(django_request)
        return response


class AttendanceActivityImportTemplateAPIView(APIView):
    """
    Download Excel template for attendance activity import.
    GET /api/v1/attendance/attendance-activity-import-template/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.http import HttpResponse

        data_frame = pd.DataFrame(
            columns=[
                "Badge ID",
                "Employee",
                "Attendance Date",
                "In Date",
                "Check In",
                "Check Out",
                "Out Date",
            ]
        )
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="activity_excel.xlsx"'
        data_frame.to_excel(response, index=False)
        return response


class AttendanceActivityImportAPIView(APIView):
    """
    Import attendance activities from Excel.
    POST with multipart/form-data, file field: activity_import
    Returns: { created_count, error_count, error_file_base64? }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from django.http import HttpResponse

        if not request.user.has_perm("attendance.add_attendanceactivity"):
            return Response({"detail": "Permission denied."}, status=403)
        file_obj = request.FILES.get("activity_import")
        if not file_obj:
            return Response(
                {"detail": "No file provided. Use field name 'activity_import'."},
                status=400,
            )
        from attendance.views.views import process_activity_dicts

        try:
            data_frame = pd.read_excel(file_obj)
        except Exception as e:
            return Response(
                {"detail": f"Invalid Excel file: {str(e)}"},
                status=400,
            )
        activity_dicts = data_frame.to_dict("records")
        if not activity_dicts:
            return Response(
                {"created_count": 0, "error_count": 0},
                status=200,
            )
        import_error_dicts = process_activity_dicts(activity_dicts)
        created_count = len(activity_dicts) - len(import_error_dicts)
        error_count = len(import_error_dicts)
        result = {"created_count": created_count, "error_count": error_count}
        if import_error_dicts:
            import base64

            error_df = pd.DataFrame(import_error_dicts)
            buffer = io.BytesIO()
            error_df.to_excel(buffer, index=False)
            buffer.seek(0)
            result["error_file_base64"] = base64.b64encode(buffer.read()).decode("ascii")
            result["error_filename"] = "ImportError.xlsx"
        return Response(result, status=200)


class TodayAttendance(APIView):
    """
    Provides the ratio of marked attendances to expected attendances for the current day.

    Method:
        get(request): Calculates and returns the attendance ratio for today.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        today = datetime.today()
        week_day = today.strftime("%A").lower()

        on_time = find_on_time(request, today=today, week_day=week_day)
        late_come = find_late_come(start_date=today)
        late_come_obj = len(late_come)

        marked_attendances = late_come_obj + on_time

        expected_attendances = find_expected_attendances(week_day=week_day)
        marked_attendances_ratio = 0
        if expected_attendances != 0:
            marked_attendances_ratio = (
                f"{(marked_attendances / expected_attendances) * 100:.2f}"
            )

        return Response(
            {
                "marked_attendances_ratio": marked_attendances_ratio,
                "on_time": on_time,
                "late_come": late_come_obj,
                "marked_attendances": marked_attendances,
                "expected_attendances": expected_attendances,
            },
            status=200,
        )


class DashboardSettingsView(APIView):
    """
    Returns attendance dashboard settings (e.g. late_come_early_out_tracking).
    Used by frontend to show/hide Late Come card.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tracking = TrackLateComeEarlyOut.objects.first()
        enable = tracking.is_enable if tracking else True
        return Response({"late_come_early_out_tracking": enable}, status=200)


class DashboardAttendanceChartView(APIView):
    """
    Returns chart data for Attendance Analytic (On Time / Late Come / Early Out by department).
    Params: date (YYYY-MM-DD), type (day|weekly|monthly|date_range), end_date (for date_range).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils.translation import gettext_lazy as _

        labels = [_("On Time"), _("Late Come"), _("Early Out")]
        start_date = request.GET.get("date") or date.today()
        if isinstance(start_date, str):
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                start_date = date.today()
        end_date = request.GET.get("end_date") or start_date
        if isinstance(end_date, str):
            try:
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                end_date = start_date
        chart_type = request.GET.get("type") or "day"
        data_set = []
        for dept in Department.objects.all():
            data_set.append(
                generate_data_set(
                    request, start_date, chart_type, end_date, dept
                )
            )
        data_set = list(filter(None, data_set))
        message = _("No records available at the moment.")
        return Response(
            {"dataSet": data_set, "labels": labels, "message": message},
            status=200,
        )


class PendingHoursChartView(APIView):
    """
    Returns chart data for Hours Chart (pending hours / worked hours by department).
    Params: month (1-12 or YYYY-MM), year.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        month_param = request.GET.get("month")
        year_param = request.GET.get("year")
        if month_param and "-" in str(month_param):
            try:
                y, m = str(month_param).split("-")[:2]
                year_param = year_param or y
                month_param = int(m)
            except (ValueError, TypeError):
                pass
        if not year_param:
            year_param = date.today().year
        if not month_param:
            month_param = date.today().month
        try:
            year = int(year_param)
            month = int(month_param)
        except (TypeError, ValueError):
            year = date.today().year
            month = date.today().month
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        month_name = month_names[month - 1] if 1 <= month <= 12 else month_names[date.today().month - 1]
        get_data = query_dict({"month": month_name, "year": year})
        records = AttendanceOverTimeFilter(get_data).qs
        labels = list(Department.objects.values_list("department", flat=True))
        data = {
            "labels": labels,
            "datasets": [
                pending_hour_data(labels, records),
                worked_hour_data(labels, records),
            ],
        }
        return Response({"data": data}, status=200)


class OnBreakEmployeesView(APIView):
    """
    Returns list of employees currently on break (early_out today).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from attendance.models import AttendanceLateComeEarlyOut

        today = date.today()
        early_outs = AttendanceLateComeEarlyOut.objects.filter(
            type="early_out",
            attendance_id__attendance_date=today,
        ).select_related("employee_id", "attendance_id")
        results = []
        for obj in early_outs:
            emp = obj.employee_id
            results.append({
                "id": obj.id,
                "employee_id": emp.id if emp else None,
                "employee_first_name": getattr(emp, "employee_first_name", "") or "",
                "employee_last_name": getattr(emp, "employee_last_name", "") or "",
                "attendance_date": obj.attendance_id.attendance_date.strftime("%Y-%m-%d") if obj.attendance_id else None,
            })
        return Response({"results": results}, status=200)


class OvertimeToApproveListView(APIView):
    """
    Paginated list of attendances with overtime to approve (validated, not yet approved).
    Same filter as dashboard_approve_overtimes.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        condition = AttendanceValidationCondition.objects.first()
        min_ot = strtime_seconds("00:00")
        if condition is not None and condition.minimum_overtime_to_approve is not None:
            min_ot = strtime_seconds(condition.minimum_overtime_to_approve)
        ot_attendances = Attendance.objects.filter(
            overtime_second__gte=min_ot,
            attendance_validated=True,
            employee_id__is_active=True,
            attendance_overtime_approve=False,
        )
        ot_attendances = filtersubordinates(
            request=request,
            perm="attendance.change_overtime",
            queryset=ot_attendances,
        )
        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get("page_size") or 10)
        page = paginator.paginate_queryset(ot_attendances, request)
        serializer = AttendanceSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class DepartmentOvertimeChartView(APIView):
    """
    Returns chart data for Department Overtime Chart (approved OT by department).
    Params: date, type (day|weekly|monthly|date_range), end_date.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils.translation import gettext_lazy as _
        from horilla import settings as horilla_settings

        start_date = request.GET.get("date") or date.today()
        if isinstance(start_date, str):
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                start_date = date.today()
        chart_type = request.GET.get("type") or "day"
        end_date = request.GET.get("end_date") or start_date
        if isinstance(end_date, str):
            try:
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                end_date = start_date
        if chart_type == "day":
            pass
        elif chart_type == "weekly":
            start_date, end_date = get_week_start_end_dates(start_date)
        elif chart_type == "monthly":
            start_date, end_date = get_month_start_end_dates(start_date)
        elif chart_type == "date_range":
            start_date = start_date
            end_date = end_date
        attendance_qs = total_attendance(
            start_date=start_date, department=None, end_date=end_date
        )
        condition = AttendanceValidationCondition.objects.first()
        min_ot = strtime_seconds("00:00")
        if condition is not None and condition.minimum_overtime_to_approve is not None:
            min_ot = strtime_seconds(condition.minimum_overtime_to_approve)
        attendances = attendance_qs.filter(
            overtime_second__gte=min_ot,
            attendance_validated=True,
            employee_id__is_active=True,
            attendance_overtime_approve=True,
        )
        departments = []
        department_total = []
        for att in attendances:
            if (
                att.employee_id
                and getattr(att.employee_id, "employee_work_info", None)
                and getattr(att.employee_id.employee_work_info, "department_id", None)
            ):
                dept_name = att.employee_id.employee_work_info.department_id.department
                if dept_name not in departments:
                    departments.append(dept_name)
                    department_total.append({"department": dept_name, "ot_hours": 0})
        for att in attendances:
            if getattr(att.employee_id, "employee_work_info", None) and att.employee_id.employee_work_info.department_id:
                department = att.employee_id.employee_work_info.department_id.department
                ot_hrs = (att.approved_overtime_second or 0) / 3600
                for d in department_total:
                    if d["department"] == department:
                        d["ot_hours"] += ot_hrs
                        break
        dataset = [{"label": "", "data": [d["ot_hours"] for d in department_total]}]
        static_url = getattr(horilla_settings, "STATIC_URL", "/static/")
        return Response(
            {
                "dataset": dataset,
                "labels": departments,
                "department_total": department_total,
                "message": _("No validated Overtimes were found"),
                "emptyImageSrc": f"/{static_url}images/ui/overtime-icon.png",
            },
            status=200,
        )


class WorkRecordsListAPIView(APIView):
    """
    Returns work records for a month: employees (paginated), month_dates, leave_dates,
    and records (employee_id, date, work_record_type, message, is_leave_record).
    Mirrors backend work_records_change_month logic.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee_filter_form = EmployeeFilter(request.GET or None)
        employees_qs = filtersubordinatesemployeemodel(
            request,
            employee_filter_form.qs,
            "attendance.view_attendance",
        )
        # Include current user's employee if available
        employees_list = list(employees_qs)
        if getattr(request.user, "employee_get", None):
            emp = request.user.employee_get
            if emp and emp not in employees_list:
                employees_list.insert(0, emp)

        month_str = request.GET.get(
            "month", f"{date.today().year}-{date.today().month}"
        )
        try:
            year, month = map(int, month_str.split("-"))
        except (ValueError, AttributeError):
            year, month = date.today().year, date.today().month

        month_dates = [
            datetime(year, month, day).date()
            for week in calendar.monthcalendar(year, month)
            for day in week
            if day
        ]

        work_records = WorkRecords.objects.filter(
            date__in=month_dates, employee_id__in=employees_list
        ).select_related("employee_id", "shift_id", "attendance_id")

        work_records_dict = {
            (wr.employee_id.id, wr.date): wr for wr in work_records
        }
        leave_dates = monthly_leave_days(month, year)

        data_items = []
        for employee in employees_list:
            employee_records = []
            for current_date in month_dates:
                work_record = work_records_dict.get((employee.id, current_date))
                if work_record is None:
                    is_holiday = current_date in leave_dates
                    if is_holiday:
                        work_record = type("Placeholder", (), {
                            "work_record_type": "HD",
                            "message": "Holiday/Company Leave",
                            "is_leave_record": False,
                            "date": current_date,
                        })()
                    elif current_date < date.today():
                        work_record = type("Placeholder", (), {
                            "work_record_type": "ABS",
                            "message": "Absent",
                            "is_leave_record": False,
                            "date": current_date,
                        })()
                    else:
                        work_record = type("Placeholder", (), {
                            "work_record_type": "DFT",
                            "message": "",
                            "is_leave_record": False,
                            "date": current_date,
                        })()
                employee_records.append((employee, work_record))
            data_items.append((employee, employee_records))

        page_size = int(request.GET.get("page_size") or get_pagination() or 50)
        paginator = Paginator(data_items, page_size)
        page_num = request.GET.get("page", 1)
        try:
            page_num = max(1, int(page_num))
        except (TypeError, ValueError):
            page_num = 1
        page = paginator.get_page(page_num)

        employees_payload = []
        records_payload = []
        for employee, employee_records in page.object_list:
            employees_payload.append({
                "id": employee.id,
                "employee_first_name": getattr(
                    employee, "employee_first_name", ""
                ) or getattr(employee, "first_name", ""),
                "employee_last_name": getattr(
                    employee, "employee_last_name", ""
                ) or getattr(employee, "last_name", ""),
            })
            for _emp, wr in employee_records:
                date_str = wr.date.strftime("%Y-%m-%d") if hasattr(
                    wr.date, "strftime"
                ) else str(wr.date)
                records_payload.append({
                    "employee_id": employee.id,
                    "date": date_str,
                    "work_record_type": getattr(
                        wr, "work_record_type", None
                    ) or "DFT",
                    "message": getattr(wr, "message", "") or "",
                    "is_leave_record": getattr(wr, "is_leave_record", False),
                })

        # Work record type choices from model (for legend / labels)
        type_choices = [
            {"value": "FDP", "label": "Present"},
            {"value": "HDP", "label": "Half Day Present"},
            {"value": "ABS", "label": "Absent"},
            {"value": "HD", "label": "Holiday/Company Leave"},
            {"value": "CONF", "label": "Conflict"},
            {"value": "DFT", "label": "Draft"},
        ]

        return Response({
            "employees": employees_payload,
            "records": records_payload,
            "month_dates": [
                d.strftime("%Y-%m-%d") for d in month_dates
            ],
            "leave_dates": [
                d.strftime("%Y-%m-%d")
                for d in leave_dates
                if hasattr(d, "strftime")
            ],
            "type_choices": type_choices,
            "pagination": {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "page": page_num,
                "page_size": page_size,
                "has_next": page.has_next(),
                "has_previous": page.has_previous(),
            },
        }, status=200)


class WorkRecordExportAPIView(APIView):
    """
    Export work records for a month as Excel. Uses JWT auth (same as other API views).
    Mirrors Django work_record_export logic but returns file for API clients.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            month = int(request.GET.get("month") or date.today().month)
            year = int(request.GET.get("year") or date.today().year)
        except (ValueError, TypeError):
            return Response(
                {"error": ["Invalid month or year parameter."]},
                status=400,
            )

        employee_filter_form = EmployeeFilter(request.GET or None)
        employees_qs = filtersubordinatesemployeemodel(
            request,
            employee_filter_form.qs,
            "attendance.view_workrecords",
        )
        employees = list(employees_qs)
        if getattr(request.user, "employee_get", None):
            emp = request.user.employee_get
            if emp and emp not in employees:
                employees.insert(0, emp)

        records = WorkRecords.objects.filter(date__month=month, date__year=year)
        num_days = calendar.monthrange(year, month)[1]
        all_date_objects = [date(year, month, day) for day in range(1, num_days + 1)]
        leave_dates = set(monthly_leave_days(month, year))

        record_lookup = defaultdict(lambda: "ABS")
        for record in records:
            if record.date <= date.today():
                record_key = (record.employee_id, record.date)
                record_lookup[record_key] = record.work_record_type

        date_format = getattr(
            getattr(request.user, "employee_get", None),
            "get_date_format",
            lambda: None,
        )()
        format_string = HORILLA_DATE_FORMATS.get(date_format, "%Y-%m-%d")
        formatted_dates = [day.strftime(format_string) for day in all_date_objects]
        data_rows = []

        for employee in employees:
            row_data = {"Employee": str(employee)}
            for day, formatted_day in zip(all_date_objects, formatted_dates):
                if day not in leave_dates and day < date.today():
                    row_data[formatted_day] = record_lookup.get((employee, day), "DFT")
                else:
                    data = record_lookup.get((employee, day), "")
                    row_data[formatted_day] = data if data != "DFT" else ""
            data_rows.append(row_data)

        columns = ["Employee"] + formatted_dates
        df = pd.DataFrame(data_rows, columns=columns)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1")
            workbook = writer.book
            worksheet = writer.sheets["Sheet1"]

            formats = {
                "ABS": workbook.add_format({"bg_color": "#808080", "font_color": "#ffffff"}),
                "FDP": workbook.add_format({"bg_color": "#38c338", "font_color": "#ffffff"}),
                "HDP": workbook.add_format({"bg_color": "#dfdf52", "font_color": "#000000"}),
                "CONF": workbook.add_format({"bg_color": "#ed4c4c", "font_color": "#ffffff"}),
                "DFT": workbook.add_format({"bg_color": "#a8b1ff", "font_color": "#ffffff"}),
            }

            for row_idx, row in enumerate(df.itertuples(index=False), start=1):
                for col_idx, cell_value in enumerate(row[1:], start=1):
                    if cell_value in formats:
                        worksheet.write(row_idx, col_idx, cell_value, formats[cell_value])

            for col_idx, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).map(len).max(), len(col))
                worksheet.set_column(col_idx, col_idx, max_len)

        output.seek(0)
        from django.http import HttpResponse

        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="work_record_export.xlsx"'
        return response


class OfflineEmployeesCountView(APIView):
    """
    Retrieves the count of active employees who have not clocked in today.

    Method:
        get(request): Returns the number of active employees who are not yet clocked in.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = (
            EmployeeFilter({"not_in_yet": date.today()})
            .qs.exclude(employee_work_info__isnull=True)
            .filter(is_active=True)
            .count()
        )
        return Response({"count": count}, status=200)


class OfflineEmployeesListView(APIView):
    """
    Lists active employees who have not clocked in today, including their leave status.

    Method:
        get(request): Retrieves and paginates a list of employees not clocked in today with their leave status.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            EmployeeFilter({"not_in_yet": date.today()})
            .qs.exclude(employee_work_info__isnull=True)
            .filter(is_active=True)
        )
        leave_status = self.get_leave_status(queryset)
        pagenation = PageNumberPagination()
        page = pagenation.paginate_queryset(leave_status, request)
        return pagenation.get_paginated_response(page)

    def get_leave_status(self, queryset):
        today = date.today()
        queryset = queryset.distinct()
        # Build Case/When for leave status; skip leave lookups if leave app not installed
        whens = []
        if apps.is_installed("leave"):
            whens = [
                When(
                    Q(
                        leaverequest_set__start_date__lte=today,
                        leaverequest_set__end_date__gte=today,
                        leaverequest_set__status="approved",
                    ),
                    then=Value("On Leave"),
                ),
                When(
                    Q(
                        leaverequest_set__start_date__lte=today,
                        leaverequest_set__end_date__gte=today,
                        leaverequest_set__status="requested",
                    ),
                    then=Value("Waiting Approval"),
                ),
                When(
                    Q(
                        leaverequest_set__start_date__lte=today,
                        leaverequest_set__end_date__gte=today,
                        leaverequest_set__status__in=["cancelled", "rejected"],
                    ),
                    then=Value("Canceled / Rejected"),
                ),
            ]
        whens.append(
            When(
                employee_attendances__attendance_date=today,
                then=Value("Working"),
            )
        )
        employees_with_leave_status = (
            queryset.annotate(
                leave_status=Case(
                    *whens,
                    default=Value("Expected working"),
                    output_field=CharField(),
                ),
                job_position_id=F("employee_work_info__job_position_id"),
            )
            .values(
                "employee_first_name",
                "employee_last_name",
                "leave_status",
                "employee_profile",
                "id",
                "job_position_id",
            )
            .distinct()
        )

        for employee in employees_with_leave_status:

            if employee["employee_profile"]:
                employee["employee_profile"] = (
                    settings.MEDIA_URL + employee["employee_profile"]
                )
        return employees_with_leave_status


class CheckingStatus(APIView):
    """
    Checks and provides the current attendance status for the authenticated user.

    Method:
        get(request): Returns the attendance status, duration at work, and clock-in time if available.
    """

    permission_classes = [IsAuthenticated]

    @classmethod
    def _format_seconds(cls, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def get(self, request):
        duration = None
        work_seconds = request.user.employee_get.get_forecasted_at_work()[
            "forecasted_at_work_seconds"
        ]
        duration = CheckingStatus._format_seconds(int(work_seconds))
        status = False
        clock_in_time = None

        today = datetime.now().date()
        
        # Get all attendance activities for today
        today_activities = AttendanceActivity.objects.filter(
            employee_id=request.user.employee_get, 
            attendance_date=today
        ).order_by("in_datetime")
        
        if today_activities.exists():
            # Get the first check-in time for today
            first_activity = today_activities.first()
            clock_in_time = first_activity.clock_in.strftime("%I:%M %p")
            
            # Check if user is currently checked in by looking at the latest activity
            latest_activity = today_activities.order_by("-id").first()
            
            # User is checked in if the latest activity doesn't have a clock_out_date
            if latest_activity and not latest_activity.clock_out_date:
                status = True
                return Response(
                    {
                        "status": status,
                        "duration": duration,
                        "clock_in": clock_in_time,
                        "clock_in_time": clock_in_time,  # Add this for mobile app compatibility
                    },
                    status=200,
                )
            else:
                # User is checked out
                status = False
                return Response(
                    {
                        "status": status,
                        "duration": duration,
                        "clock_in": clock_in_time,
                        "clock_in_time": clock_in_time,  # Add this for mobile app compatibility
                    },
                    status=200,
                )
        
        # No activities for today
        return Response(
            {"status": status, "duration": duration, "clock_in_time": clock_in_time},
            status=200,
        )


class MailTemplateView(APIView):
    """
    Retrieves a list of recruitment mail templates.

    Method:
        get(request): Returns all recruitment mail templates.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        instances = HorillaMailTemplate.objects.all()
        serializer = MailTemplateSerializer(instances, many=True)
        return Response(serializer.data, status=200)


class ConvertedMailTemplateConvert(APIView):
    """
    Renders a recruitment mail template with data from a specified employee.

    Method:
        put(request): Renders the mail template body with employee and user data and returns the result.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request):
        template_id = request.data.get("template_id", None)
        employee_id = request.data.get("employee_id", None)
        employee = Employee.objects.filter(id=employee_id).first()
        bdy = HorillaMailTemplate.objects.filter(id=template_id).first()
        if not bdy:
            return Response({"error": "Template not found"}, status=404)
        if not employee:
            return Response({"error": "Employee not found"}, status=404)
        template_bdy = template.Template(bdy.body)
        context = template.Context(
            {"instance": employee, "self": request.user.employee_get}
        )
        render_bdy = template_bdy.render(context)
        return Response(render_bdy)


class OfflineEmployeeMailsend(APIView):
    """
    Sends an email with attachments and rendered templates to a specified employee.

    Method:
        post(request): Renders email templates with employee and user data, attaches files, and sends the email.
    """

    permission_classes = [IsAuthenticated]

    # def post(self, request):
    #     employee_id = request.POST.get("employee_id")
    #     subject = request.POST.get("subject", "")
    #     bdy = request.POST.get("body", "")
    #     other_attachments = request.FILES.getlist("other_attachments")
    #     attachments = [
    #         (file.name, file.read(), file.content_type) for file in other_attachments
    #     ]
    #     email_backend = ConfiguredEmailBackend()
    #     host = email_backend.dynamic_username
    #     employee = Employee.objects.get(id=employee_id)
    #     template_attachment_ids = request.POST.getlist("template_attachments")
    #     bodys = list(
    #         HorillaMailTemplate.objects.filter(
    #             id__in=template_attachment_ids
    #         ).values_list("body", flat=True)
    #     )
    #     for html in bodys:
    #         # due to not having solid template we first need to pass the context
    #         template_bdy = template.Template(html)
    #         context = template.Context(
    #             {"instance": employee, "self": request.user.employee_get}
    #         )
    #         render_bdy = template_bdy.render(context)
    #         attachments.append(
    #             (
    #                 "Document",
    #                 generate_pdf(render_bdy, {}, path=False, title="Document").content,
    #                 "application/pdf",
    #             )
    #         )

    #     template_bdy = template.Template(bdy)
    #     context = template.Context(
    #         {"instance": employee, "self": request.user.employee_get}
    #     )
    #     render_bdy = template_bdy.render(context)

    #     email = EmailMessage(
    #         subject,
    #         render_bdy,
    #         host,
    #         [employee.employee_work_info.email],
    #     )
    #     email.content_subtype = "html"

    #     email.attachments = attachments
    #     try:
    #         email.send()
    #         if employee.employee_work_info.email:
    #             return Response(f"Mail sent to {employee.get_full_name()}")
    #         else:
    #             return Response(f"Email not set for {employee.get_full_name()}")
    #     except Exception as e:
    #         return Response("Something went wrong")

    def post(self, request):
      # Handle both JSON and form data
      if request.content_type == 'application/json':
        employee_id = request.data.get("employee_id")
        subject = request.data.get("subject", "")
        bdy = request.data.get("body", "")
        template_attachment_ids = request.data.get("template_attachments", [])
        other_attachments = []
      else:
        employee_id = request.POST.get("employee_id")
        subject = request.POST.get("subject", "")
        bdy = request.POST.get("body", "")
        template_attachment_ids = request.POST.getlist("template_attachments")
        other_attachments = request.FILES.getlist("other_attachments")
    
      if not employee_id:
        return Response({"error": "employee_id is required"}, status=400)
    
      attachments = [
        (file.name, file.read(), file.content_type) for file in other_attachments
       ]
      email_backend = ConfiguredEmailBackend()
      host = email_backend.dynamic_username
    
      try:
        employee = Employee.objects.get(id=employee_id)
      except Employee.DoesNotExist:
        return Response({"error": f"Employee with id {employee_id} does not exist"}, status=404)
    
      bodys = list(
        HorillaMailTemplate.objects.filter(
            id__in=template_attachment_ids
        ).values_list("body", flat=True)
      )
      for html in bodys:
        # due to not having solid template we first need to pass the context
        template_bdy = template.Template(html)
        context = template.Context(
            {"instance": employee, "self": request.user.employee_get}
        )
        render_bdy = template_bdy.render(context)
        attachments.append(
            (
                "Document",
                generate_pdf(render_bdy, {}, path=False, title="Document").content,
                "application/pdf",
            )
        )

      template_bdy = template.Template(bdy)
      context = template.Context(
        {"instance": employee, "self": request.user.employee_get}
      )
      render_bdy = template_bdy.render(context)

      # Check if employee has email
      if not (employee.employee_work_info and employee.employee_work_info.email):
        return Response({"error": f"Email not set for {employee.get_full_name()}"}, status=400)

      email = EmailMessage(
        subject,
        render_bdy,
        host,
        [employee.employee_work_info.email],
      )
      email.content_subtype = "html"

      email.attachments = attachments
      try:
        email.send()
        return Response({"message": f"Mail sent to {employee.get_full_name()}"}, status=200)
      except Exception as e:
        return Response({"error": "Something went wrong while sending email"}, status=500)