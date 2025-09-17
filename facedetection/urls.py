from django.urls import path

from .views import *

urlpatterns = [
    path("config/", FaceDetectionConfigAPIView.as_view()),
    path("setup/", EmployeeFaceDetectionGetPostAPIView.as_view()),
    path("employee-registration/", employee_face_registration, name="employee-face-registration"),
    path("employee-delete/", employee_face_delete, name="employee-face-delete"),
    path("employee-profile-face/", employee_profile_with_face, name="employee-profile-face"),
    path("attendance-interface/", face_attendance_interface, name="face-attendance-interface"),
    path("attendance-clock-in/", face_attendance_clock_in, name="face-attendance-clock-in"),
    path("attendance-clock-out/", face_attendance_clock_out, name="face-attendance-clock-out"),
    path("", face_detection_config, name="face-config"),
]
