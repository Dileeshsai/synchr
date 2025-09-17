from django.urls import path, include
from ...api_views.facedetection.views import (
    FaceDetectionConfigAPIView,
    EmployeeFaceDetectionGetPostAPIView,
    FaceVerificationAPIView,
    FaceImageValidationAPIView,
    FaceDetectionStatusAPIView,
    BulkFaceRegistrationAPIView,
    FaceRecognitionStatsAPIView,
    EmployeeFaceDetectionDetailAPIView,
    quick_face_checkin,
    quick_face_checkout,
)

urlpatterns = [
    # Face Detection Configuration
    path('config/', FaceDetectionConfigAPIView.as_view(), name='face-detection-config'),
    
    # Employee Face Detection Records
    path('employees/', EmployeeFaceDetectionGetPostAPIView.as_view(), name='employee-face-detection-list'),
    path('employees/<int:pk>/', EmployeeFaceDetectionDetailAPIView.as_view(), name='employee-face-detection-detail'),
    
    # Face Verification and Attendance
    path('verify/', FaceVerificationAPIView.as_view(), name='face-verification'),
    path('checkin/', quick_face_checkin, name='quick-face-checkin'),
    path('checkout/', quick_face_checkout, name='quick-face-checkout'),
    
    # Face Image Validation
    path('validate-image/', FaceImageValidationAPIView.as_view(), name='face-image-validation'),
    
    # Face Detection Status
    path('status/', FaceDetectionStatusAPIView.as_view(), name='face-detection-status'),
    
    # Bulk Operations
    path('bulk-register/', BulkFaceRegistrationAPIView.as_view(), name='bulk-face-registration'),
    
    # Statistics
    path('stats/', FaceRecognitionStatsAPIView.as_view(), name='face-recognition-stats'),
]
