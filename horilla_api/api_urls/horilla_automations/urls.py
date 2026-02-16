from django.urls import path, re_path

from ...api_views.horilla_automations.views import (
    MailAutomationGetToFieldView,
    MailAutomationLoadView,
    MailAutomationModelChoicesView,
    MailAutomationRefreshView,
    MailAutomationView,
)

urlpatterns = [
    re_path(
        r"^automations/(?P<pk>\d+)?$",
        MailAutomationView.as_view(),
        name="api-mail-automation-detail",
    ),
    path(
        "model-choices/",
        MailAutomationModelChoicesView.as_view(),
        name="api-mail-automation-model-choices",
    ),
    path(
        "get-to-field/",
        MailAutomationGetToFieldView.as_view(),
        name="api-mail-automation-get-to-field",
    ),
    path(
        "load/",
        MailAutomationLoadView.as_view(),
        name="api-mail-automation-load",
    ),
    path(
        "refresh/",
        MailAutomationRefreshView.as_view(),
        name="api-mail-automation-refresh",
    ),
]
