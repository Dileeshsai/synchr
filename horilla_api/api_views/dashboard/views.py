"""
Main Dashboard API - aligned with backend Django dashboard layout.
Returns top cards, birthdays, announcements, on leave today - all from backend, no hardcoded data.
"""
import calendar
from datetime import date, datetime, timedelta

from django.apps import apps
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.utils.translation import gettext as _
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from employee.models import Employee, EmployeeWorkInformation
from horilla.methods import get_horilla_model_class


class MainDashboardAPIView(APIView):
    """
    Main dashboard data - mirrors backend dashboard.html sections.
    Top cards: New Joining Today, New Joining This Week, Total Strength.
    Sidebar: Birthdays, Announcements, On Leave Today.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "top_cards": self._get_top_cards(request),
            "birthdays": self._get_birthdays(request),
            "announcements": self._get_announcements(request),
            "on_leave_today": self._get_on_leave_today(request),
            "permissions": {
                "show_top_cards": request.user.has_perm("employee.view_employee"),
                "show_recruitment_cards": apps.is_installed("recruitment"),
                "show_birthdays": request.user.has_perm("employee.view_employee"),
                "show_announcements": True,
                "show_on_leave": apps.is_installed("leave")
                and (
                    request.user.has_perm("leave.view_leaverequest")
                    or self._is_reporting_manager(request)
                ),
                "show_employee_work_info": (
                    request.user.has_perm("employee.view_employeeworkinformation")
                    or self._is_reporting_manager(request)
                ),
                "show_attendance_tiles": apps.is_installed("attendance")
                and (
                    request.user.has_perm("employee.view_employee")
                    or self._is_reporting_manager(request)
                ),
                "show_leave_requests_tile": apps.is_installed("leave")
                and (
                    request.user.has_perm("leave.change_leaverequest")
                    or self._is_reporting_manager(request)
                ),
                "show_attendance_validate_tile": apps.is_installed("attendance")
                and (
                    request.user.has_perm("attendance.change_attendance")
                    or self._is_reporting_manager(request)
                ),
                "show_overtime_approve_tile": apps.is_installed("attendance")
                and (
                    request.user.has_perm("attendance.change_attendance")
                    or self._is_reporting_manager(request)
                ),
                "show_shift_requests_tile": (
                    request.user.has_perm("base.change_shiftrequest")
                    or self._is_reporting_manager(request)
                ),
                "show_work_type_requests_tile": (
                    request.user.has_perm("base.change_worktyperequest")
                    or self._is_reporting_manager(request)
                ),
                "show_leave_allocation_tile": apps.is_installed("leave")
                and (
                    request.user.has_perm("leave.change_leaveallocationrequest")
                    or self._is_reporting_manager(request)
                ),
                "show_asset_requests_tile": apps.is_installed("asset")
                and request.user.has_perm("asset.change_assetrequest"),
                "show_feedback_answer_tile": apps.is_installed("pms")
                and (
                    request.user.has_perm("pms.view_feedback")
                    or self._is_reporting_manager(request)
                ),
            },
        }
        return Response(data, status=200)

    def _is_reporting_manager(self, request):
        try:
            from base.methods import is_reportingmanager
            return is_reportingmanager(request.user)
        except Exception:
            return False

    def _get_top_cards(self, request):
        if not request.user.has_perm("employee.view_employee"):
            return {}

        result = {
            "total_strength": Employee.objects.filter(is_active=True).count(),
            "new_joining_today": 0,
            "new_joining_week": 0,
        }

        if apps.is_installed("recruitment"):
            try:
                Candidate = get_horilla_model_class(
                    app_label="recruitment", model="candidate"
                )
                today = date.today()
                result["new_joining_today"] = Candidate.objects.filter(
                    joining_date__range=[today, today + timedelta(days=1)],
                    is_active=True,
                ).count()

                first_day = today - timedelta(days=today.weekday())
                last_day = today + timedelta(days=6 - today.weekday())
                result["new_joining_week"] = Candidate.objects.filter(
                    joining_date__range=[first_day, last_day],
                    is_active=True,
                    hired=True,
                ).count()
            except Exception:
                pass

        return result

    def _get_birthdays(self, request):
        if not request.user.has_perm("employee.view_employee"):
            return []

        today = date.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        employees = (
            Employee.objects.filter(
                is_active=True,
                dob__isnull=False,
                dob__day__gte=today.day,
                dob__month=today.month,
                dob__day__lte=last_day,
            )
            .order_by(F("dob__day").asc(nulls_last=True))
            [:20]
        )

        default_avatar = "https://ui-avatars.com/api/?background=random&name="
        birthdays = []
        for emp in employees:
            days_until = emp.days_until_birthday

            days_label = (
                _("Today")
                if days_until == 0
                else (_("Tomorrow") if days_until == 1 else f"In {days_until} Days")
            )
            dept = emp.get_department()
            job = emp.get_job_position()
            birthdays.append(
                {
                    "id": emp.id,
                    "name": f"{emp.employee_first_name} {emp.employee_last_name}",
                    "profile": (
                        emp.get_avatar()
                        if hasattr(emp, "get_avatar")
                        else f"{default_avatar}{emp.employee_first_name}+{emp.employee_last_name}"
                    ),
                    "dob": emp.dob.strftime("%d %b") if emp.dob else "",
                    "days_until_birthday": days_label,
                    "department": dept.department if dept else "",
                    "job_position": job.job_position if job else "",
                }
            )
        return birthdays

    def _get_announcements(self, request):
        try:
            from base.models import Announcement, AnnouncementExpire
            from django.db.models import Q
        except ImportError:
            return []

        expire_days = 30
        try:
            expire = AnnouncementExpire.objects.first()
            if expire:
                expire_days = expire.days
        except Exception:
            pass

        today = date.today()
        qs = Announcement.objects.filter(expire_date__gte=today).order_by("-created_at")

        has_view = request.user.has_perm("base.view_announcement")
        if not has_view:
            emp = getattr(request.user, "employee_get", None)
            if emp:
                qs = qs.filter(
                    Q(employees=emp) | Q(employees__isnull=True)
                ).distinct()
            else:
                qs = qs.filter(employees__isnull=True)

        announcements = []
        for a in qs[:15]:
            announcements.append(
                {
                    "id": a.id,
                    "title": a.title or "",
                    "description": (a.description or "")[:200],
                    "created_at": (
                        a.created_at.strftime("%b %d, %Y")
                        if hasattr(a, "created_at") and a.created_at
                        else ""
                    ),
                    "expire_date": (
                        a.expire_date.strftime("%Y-%m-%d") if a.expire_date else None
                    ),
                }
            )
        return announcements

    def _get_on_leave_today(self, request):
        if not apps.is_installed("leave"):
            return []
        try:
            from leave.models import LeaveRequest

            leaves = LeaveRequest.employees_on_leave_today(status="approved")
            result = []
            for lv in leaves[:20]:
                emp = lv.employee_id
                result.append(
                    {
                        "id": lv.id,
                        "employee_id": emp.id if emp else None,
                        "employee_name": (
                            f"{emp.employee_first_name} {emp.employee_last_name}"
                            if emp
                            else ""
                        ),
                        "leave_type": (
                            lv.leave_type_id.name if lv.leave_type_id else ""
                        ),
                        "start_date": (
                            lv.start_date.strftime("%Y-%m-%d") if lv.start_date else ""
                        ),
                        "end_date": (
                            lv.end_date.strftime("%Y-%m-%d") if lv.end_date else ""
                        ),
                        "requested_days": float(lv.requested_days) if lv.requested_days else 0,
                    }
                )
            return result
        except Exception:
            return []


class EmployeeWorkInfoCompleteAPIView(APIView):
    """
    Employees with incomplete work information - for dashboard sidebar.
    Mirrors backend emp-workinfo-complete (work_info_complete.html).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (
            request.user.has_perm("employee.view_employeeworkinformation")
            or self._is_reporting_manager(request)
        ):
            return Response({"results": [], "total": 0, "page": 1, "pages": 0})

        fields_to_focus = [
            "job_position_id",
            "department_id",
            "work_type_id",
            "employee_type_id",
            "job_role_id",
            "reporting_manager_id",
            "company_id",
            "location",
            "email",
            "mobile",
            "shift_id",
            "date_joining",
            "contract_end_date",
            "basic_salary",
            "salary_hour",
        ]
        search = request.GET.get("search", "").strip()
        page = int(request.GET.get("page", 1))
        per_page = min(int(request.GET.get("page_size", 10)), 50)

        from base.methods import filtersubordinates, filtersubordinatesemployeemodel

        employees_with_pending = []

        # Employees with work info but incomplete (< 15 fields)
        employees_workinfos = filtersubordinates(
            request,
            queryset=EmployeeWorkInformation.objects.filter(
                employee_id__employee_first_name__icontains=search,
                employee_id__is_active=True,
            ).select_related("employee_id"),
            perm="employee.view_employeeworkinformation",
        )
        for work_info in employees_workinfos:
            completed = sum(
                1 for f in fields_to_focus if getattr(work_info, f) is not None
            )
            if completed < 15:
                emp = work_info.employee_id
                percent = round((completed / 15) * 100, 1)
                employees_with_pending.append(
                    {
                        "employee_id": emp.id,
                        "employee_name": f"{emp.employee_first_name} {emp.employee_last_name}",
                        "badge_id": emp.badge_id or "",
                        "completed_percent": percent,
                    }
                )

        # Employees with NO work info
        emps_no_workinfo = filtersubordinatesemployeemodel(
            request,
            Employee.objects.filter(employee_work_info__isnull=True)
            .filter(employee_first_name__icontains=search)
            .filter(is_active=True),
            perm="employee.view_employeeworkinformation",
        )
        for emp in emps_no_workinfo:
            employees_with_pending.insert(
                0,
                {
                    "employee_id": emp.id,
                    "employee_name": f"{emp.employee_first_name} {emp.employee_last_name}",
                    "badge_id": emp.badge_id or "",
                    "completed_percent": 0,
                },
            )

        employees_with_pending.sort(key=lambda x: x["completed_percent"])

        paginator = Paginator(employees_with_pending, per_page)
        page_obj = paginator.get_page(page)

        return Response(
            {
                "results": list(page_obj.object_list),
                "total": paginator.count,
                "page": page,
                "pages": paginator.num_pages,
            },
            status=200,
        )

    def _is_reporting_manager(self, request):
        try:
            from base.methods import is_reportingmanager
            return is_reportingmanager(request.user)
        except Exception:
            return False


class LeaveRequestsToApproveAPIView(APIView):
    """
    Leave requests pending approval - for dashboard tile.
    Mirrors backend leave_request_and_approve (leave_request_approve.html).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not apps.is_installed("leave"):
            return Response({"results": [], "total": 0, "page": 1, "pages": 0})
        if not (
            request.user.has_perm("leave.change_leaverequest")
            or self._is_rm(request)
        ):
            return Response({"results": [], "total": 0, "page": 1, "pages": 0})

        from base.methods import filtersubordinates
        from leave.models import LeaveRequest, LeaveRequestConditionApproval

        leave_requests = LeaveRequest.objects.filter(
            status="requested",
            employee_id__is_active=True,
            start_date__gte=date.today(),
        ).select_related("employee_id", "leave_type_id")
        leave_requests = filtersubordinates(
            request, leave_requests, "leave.change_leaverequest"
        )

        multi_approve = LeaveRequestConditionApproval.objects.filter(
            is_approved=False, is_rejected=False
        )
        if multi_approve.exists():
            multi_ids = list(multi_approve.values_list("leave_request_id_id", flat=True))
            leave_requests = leave_requests.exclude(id__in=multi_ids)

        page_num = int(request.GET.get("page", 1))
        per_page = min(int(request.GET.get("page_size", 8)), 50)
        paginator = Paginator(list(leave_requests), per_page)
        page_obj = paginator.get_page(page_num)

        results = []
        for lr in page_obj.object_list:
            emp = lr.employee_id
            results.append(
                {
                    "id": lr.id,
                    "employee_id": emp.id if emp else None,
                    "employee_name": (
                        f"{emp.employee_first_name} {emp.employee_last_name}"
                        if emp
                        else ""
                    ),
                    "leave_type": lr.leave_type_id.name if lr.leave_type_id else "",
                    "start_date": lr.start_date.strftime("%Y-%m-%d") if lr.start_date else "",
                    "end_date": lr.end_date.strftime("%Y-%m-%d") if lr.end_date else "",
                    "requested_days": float(lr.requested_days) if lr.requested_days else 0,
                }
            )

        return Response(
            {
                "results": results,
                "total": paginator.count,
                "page": page_num,
                "pages": paginator.num_pages,
            },
            status=200,
        )

    def _is_rm(self, request):
        try:
            from base.methods import is_reportingmanager
            return is_reportingmanager(request.user)
        except Exception:
            return False


class LeaveRequestsToApproveAPIView(APIView):
    """
    Leave requests pending approval - for dashboard tile.
    Mirrors backend leave_request_and_approve (leave_request_approve.html).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not apps.is_installed("leave"):
            return Response({"results": [], "total": 0, "page": 1, "pages": 0})
        if not (
            request.user.has_perm("leave.change_leaverequest")
            or self._is_reporting_manager_leave(request)
        ):
            return Response({"results": [], "total": 0, "page": 1, "pages": 0})

        from base.methods import filtersubordinates
        from leave.models import LeaveRequest, LeaveRequestConditionApproval

        leave_requests = LeaveRequest.objects.filter(
            status="requested",
            employee_id__is_active=True,
            start_date__gte=date.today(),
        ).select_related("employee_id", "leave_type_id")
        leave_requests = filtersubordinates(
            request, leave_requests, "leave.change_leaverequest"
        )

        multi_approve = LeaveRequestConditionApproval.objects.filter(
            is_approved=False, is_rejected=False
        )
        if multi_approve.exists():
            multi_ids = list(multi_approve.values_list("leave_request_id_id", flat=True))
            leave_requests = leave_requests.exclude(id__in=multi_ids)

        page = int(request.GET.get("page", 1))
        per_page = min(int(request.GET.get("page_size", 8)), 50)
        paginator = Paginator(list(leave_requests), per_page)
        page_obj = paginator.get_page(page)

        results = []
        for lr in page_obj.object_list:
            emp = lr.employee_id
            results.append(
                {
                    "id": lr.id,
                    "employee_id": emp.id if emp else None,
                    "employee_name": (
                        f"{emp.employee_first_name} {emp.employee_last_name}"
                        if emp
                        else ""
                    ),
                    "leave_type": lr.leave_type_id.name if lr.leave_type_id else "",
                    "start_date": lr.start_date.strftime("%Y-%m-%d") if lr.start_date else "",
                    "end_date": lr.end_date.strftime("%Y-%m-%d") if lr.end_date else "",
                    "requested_days": float(lr.requested_days) if lr.requested_days else 0,
                }
            )

        return Response(
            {
                "results": results,
                "total": paginator.count,
                "page": page,
                "pages": paginator.num_pages,
            },
            status=200,
        )

    def _is_reporting_manager_leave(self, request):
        try:
            from base.methods import is_reportingmanager
            return is_reportingmanager(request.user)
        except Exception:
            return False


class FeedbacksToAnswerAPIView(APIView):
    """
    Feedbacks the current user is requested to answer but hasn't yet.
    Mirrors backend dashboard_feedback_answer.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not apps.is_installed("pms"):
            return Response({"results": [], "total": 0, "page": 1, "pages": 0})
        if not (
            request.user.has_perm("pms.view_feedback")
            or self._is_reporting_manager(request)
        ):
            return Response({"results": [], "total": 0, "page": 1, "pages": 0})

        employee = getattr(request.user, "employee_get", None)
        if not employee:
            return Response({"results": [], "total": 0, "page": 1, "pages": 0})

        from pms.models import Feedback

        feedback_requested = Feedback.objects.filter(
            Q(manager_id=employee, manager_id__is_active=True)
            | Q(colleague_id=employee, colleague_id__is_active=True)
            | Q(subordinate_id=employee, subordinate_id__is_active=True)
        ).filter(archive=False).distinct()
        feedbacks = feedback_requested.exclude(
            feedback_answer__employee_id=employee
        )

        page_num = int(request.GET.get("page", 1))
        per_page = min(int(request.GET.get("page_size", 8)), 50)
        paginator = Paginator(list(feedbacks), per_page)
        page_obj = paginator.get_page(page_num)

        results = []
        for fb in page_obj.object_list:
            emp = fb.employee_id
            results.append(
                {
                    "id": fb.id,
                    "review_cycle": fb.review_cycle or "",
                    "employee_name": (
                        f"{emp.employee_first_name} {emp.employee_last_name}"
                        if emp
                        else ""
                    ),
                    "start_date": (
                        fb.start_date.strftime("%Y-%m-%d") if fb.start_date else ""
                    ),
                    "end_date": (
                        fb.end_date.strftime("%Y-%m-%d") if fb.end_date else ""
                    ),
                }
            )

        return Response(
            {
                "results": results,
                "total": paginator.count,
                "page": page_num,
                "pages": paginator.num_pages,
            },
            status=200,
        )

    def _is_reporting_manager(self, request):
        try:
            from base.methods import is_reportingmanager
            return is_reportingmanager(request.user)
        except Exception:
            return False
