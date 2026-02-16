"""
horilla_api/urls/attendance/urls.py
"""

from django.urls import path

from horilla_api.api_views.attendance.permission_views import AttendancePermissionCheck
from horilla_api.api_views.attendance.views import *

urlpatterns = [
    # attendance-request* must come before "attendance/" so /attendance/attendance-request/ matches
    path(
        "attendance-request/",
        AttendanceRequestView.as_view(),
        name="api-attendance-request-view",
    ),
    path(
        "attendance-request-bulk/",
        AttendanceRequestBulkCreateAPIView.as_view(),
        name="api-attendance-request-bulk",
    ),
    path(
        "attendance-request/<int:pk>",
        AttendanceRequestView.as_view(),
        name="api-attendance-request-detail",
    ),
    path(
        "attendance-request-approve/<int:pk>",
        AttendanceRequestApproveView.as_view(),
        name="api-attendance-request-approve",
    ),
    path(
        "attendance-request-cancel/<int:pk>",
        AttendanceRequestCancelView.as_view(),
        name="api-attendance-request-cancel",
    ),
    path("batches/", BatchListAPIView.as_view(), name="api-attendance-batches"),
    path("batches/<int:pk>/", BatchDetailAPIView.as_view(), name="api-attendance-batch-detail"),
    path(
        "attendance-request-add-to-batch/",
        AttendanceRequestAddToBatchAPIView.as_view(),
        name="api-attendance-request-add-to-batch",
    ),
    path(
        "attendance-request-ids/",
        AttendanceRequestIdsView.as_view(),
        name="api-attendance-request-ids",
    ),
    path(
        "attendance-request-validate-detail/<int:pk>/",
        AttendanceRequestValidateDetailView.as_view(),
        name="api-attendance-request-validate-detail",
    ),
    path(
        "attendance-request/<int:pk>/comments/",
        AttendanceRequestCommentsAPIView.as_view(),
        name="api-attendance-request-comments",
    ),
    path(
        "attendance-request/<int:pk>/comments/<int:comment_id>/",
        AttendanceRequestCommentDeleteAPIView.as_view(),
        name="api-attendance-request-comment-delete",
    ),
    path("clock-in/", ClockInAPIView.as_view(), name="api-check-in"),
    path("clock-out/", ClockOutAPIView.as_view(), name="api-check-out"),
    path("attendance/", AttendanceView.as_view(), name="api-attendance-list"),
    path("attendance/<int:pk>/", AttendanceView.as_view(), name="api-attendance-detail"),
    path("attendance/<int:pk>", AttendanceView.as_view(), name="api-attendance-detail-no-slash"),
    path(
        "attendance/list/<str:type>",
        AttendanceView.as_view(),
        name="api-attendance-list",
    ),
    path("attendance-validate/<int:pk>", ValidateAttendanceView.as_view()),
    path("attendance-bulk-validate/", AttendanceBulkValidateView.as_view(), name="api-attendance-bulk-validate"),
    path("attendance-bulk-delete/", AttendanceBulkDeleteView.as_view(), name="api-attendance-bulk-delete"),
    path("overtime-approve/<int:pk>", OvertimeApproveView.as_view(), name="api-"),
    path(
        "attendance-hour-account/<int:pk>/",
        AttendanceOverTimeView.as_view(),
        name="api-",
    ),
    path("attendance-hour-account/", AttendanceOverTimeView.as_view(), name="api-"),
    path(
        "attendance-hour-account-ids/",
        AttendanceHourAccountIdsView.as_view(),
        name="api-attendance-hour-account-ids",
    ),
    path("late-come-early-out-view/", LateComeEarlyOutView.as_view(), name="api-"),
    path("late-come-early-out-view/<int:pk>/", LateComeEarlyOutView.as_view(), name="api-"),
    path("late-come-early-out-export/", LateComeEarlyOutExportAPIView.as_view(), name="api-late-come-early-out-export"),
    path(
        "validation-condition/",
        ValidationConditionAPIView.as_view(),
        name="api-validation-condition",
    ),
    path(
        "validation-condition/<int:pk>/",
        ValidationConditionAPIView.as_view(),
        name="api-validation-condition-detail",
    ),
    path(
        "break-point/",
        ValidationConditionAPIView.as_view(),
        name="api-break-point",
    ),
    path(
        "break-point/<int:pk>/",
        ValidationConditionAPIView.as_view(),
        name="api-break-point-detail",
    ),
    path(
        "check-in-out-settings/",
        AttendanceGeneralSettingAPIView.as_view(),
        name="api-check-in-out-settings",
    ),
    path(
        "check-in-out-settings/<int:pk>/",
        AttendanceGeneralSettingAPIView.as_view(),
        name="api-check-in-out-settings-detail",
    ),
    path(
        "grace-time/",
        GraceTimeAPIView.as_view(),
        name="api-grace-time-list",
    ),
    path(
        "grace-time/<int:pk>/",
        GraceTimeAPIView.as_view(),
        name="api-grace-time-detail",
    ),
    path("attendance-activity/", AttendanceActivityView.as_view(), name="api-"),
    path("attendance-activity-bulk-delete/", AttendanceActivityBulkDeleteView.as_view(), name="api-attendance-activity-bulk-delete"),
    path("attendance-activity-export/", AttendanceActivityExportAPIView.as_view(), name="api-attendance-activity-export"),
    path("attendance-activity-export-columns/", AttendanceActivityExportColumnsAPIView.as_view(), name="api-attendance-activity-export-columns"),
    path("attendance-activity-import-template/", AttendanceActivityImportTemplateAPIView.as_view(), name="api-attendance-activity-import-template"),
    path("attendance-activity-import/", AttendanceActivityImportAPIView.as_view(), name="api-attendance-activity-import"),
    path("today-attendance/", TodayAttendance.as_view(), name="api-"),
    path("dashboard-settings/", DashboardSettingsView.as_view(), name="api-dashboard-settings"),
    path("dashboard-attendance-chart/", DashboardAttendanceChartView.as_view(), name="api-dashboard-attendance-chart"),
    path("pending-hours-chart/", PendingHoursChartView.as_view(), name="api-pending-hours-chart"),
    path("on-break-employees/", OnBreakEmployeesView.as_view(), name="api-on-break-employees"),
    path("overtime-to-approve/", OvertimeToApproveListView.as_view(), name="api-overtime-to-approve"),
    path("department-overtime-chart/", DepartmentOvertimeChartView.as_view(), name="api-department-overtime-chart"),
    path("work-records/", WorkRecordsListAPIView.as_view(), name="api-work-records-list"),
    path("work-record-export/", WorkRecordExportAPIView.as_view(), name="api-work-record-export"),
    path("offline-employees/count/", OfflineEmployeesCountView.as_view(), name="api-"),
    path("offline-employees/list/", OfflineEmployeesListView.as_view(), name="api-"),
    path("online-employees/count/", OnlineEmployeesCountView.as_view(), name="api-"),
    path("online-employees/list/", OnlineEmployeesListView.as_view(), name="api-"),
    path("permission-check/attendance", AttendancePermissionCheck.as_view()),
    path("checking-in", CheckingStatus.as_view()),
    path("checking-out", CheckingStatus.as_view()),
    path("offline-employee-mail-send", OfflineEmployeeMailsend.as_view()),
    path("converted-mail-template", ConvertedMailTemplateConvert.as_view()),
    path("mail-templates", MailTemplateView.as_view()),
]
