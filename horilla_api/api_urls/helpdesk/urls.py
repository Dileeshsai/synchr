from django.urls import path
from ...api_views.helpdesk import views

urlpatterns = [
    path("tickets/", views.TicketAPIView.as_view(), name="api-ticket-list"),
    path("tickets/<int:pk>/", views.TicketAPIView.as_view(), name="api-ticket-detail"),
    path("ticket-types/", views.TicketTypeAPIView.as_view(), name="api-ticket-type-list"),
    path("ticket-types/<int:pk>/", views.TicketTypeAPIView.as_view(), name="api-ticket-type-detail"),
    path("comments/", views.CommentAPIView.as_view(), name="api-comment-list"),
    path("comments/<int:pk>/", views.CommentAPIView.as_view(), name="api-comment-detail"),
    path("attachments/", views.AttachmentAPIView.as_view(), name="api-attachment-list"),
    path("attachments/<int:pk>/", views.AttachmentAPIView.as_view(), name="api-attachment-detail"),
    path("faqs/", views.FAQAPIView.as_view(), name="api-faq-list"),
    path("faqs/<int:pk>/", views.FAQAPIView.as_view(), name="api-faq-detail"),
    path("faq-categories/", views.FAQCategoryAPIView.as_view(), name="api-faq-category-list"),
    path("faq-categories/<int:pk>/", views.FAQCategoryAPIView.as_view(), name="api-faq-category-detail"),
    path("department-managers/", views.DepartmentManagerAPIView.as_view(), name="api-department-manager-list"),
    path("department-managers/<int:pk>/", views.DepartmentManagerAPIView.as_view(), name="api-department-manager-detail"),
    path("claim-requests/", views.ClaimRequestAPIView.as_view(), name="api-claim-request-list"),
    path("claim-requests/<int:pk>/", views.ClaimRequestAPIView.as_view(), name="api-claim-request-detail"),
]

