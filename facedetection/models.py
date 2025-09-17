import os

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

# Create your models here.


class FaceDetection(models.Model):
    company_id = models.OneToOneField(
        "base.Company",
        related_name="face_detection",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    start = models.BooleanField(default=False)

    def clean(self):
        # Only validate if company_id is not None
        if self.company_id is not None:
            # Check if another FaceDetection exists for the same company
            qs = FaceDetection.objects.filter(company_id=self.company_id)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    f"Face detection configuration already exists for company {self.company_id}."
                )

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensures `clean()` runs
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company_id"],
                name="unique_company_id_when_not_null_facedetection",
                condition=~models.Q(company_id=None),
            )
        ]


class EmployeeFaceDetection(models.Model):
    employee_id = models.OneToOneField(
        "employee.Employee", related_name="face_detection", on_delete=models.CASCADE
    )
    image = models.ImageField()


class FaceRecognitionAttendanceLog(models.Model):
    """
    Model to store captured images as proof of attendance
    """
    employee_id = models.ForeignKey(
        "employee.Employee", 
        related_name="face_attendance_logs", 
        on_delete=models.CASCADE,
        verbose_name=_("Employee")
    )
    attendance_id = models.ForeignKey(
        "attendance.Attendance",
        related_name="face_recognition_logs",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Attendance Record")
    )
    captured_image = models.ImageField(
        upload_to='face_attendance_proof/%Y/%m/%d/',
        verbose_name=_("Captured Image")
    )
    action = models.CharField(
        max_length=20,
        choices=[
            ('check_in', _('Check In')),
            ('check_out', _('Check Out')),
        ],
        verbose_name=_("Action")
    )
    recognition_confidence = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Recognition Confidence")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Timestamp")
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address")
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("User Agent")
    )

    class Meta:
        verbose_name = _("Face Recognition Attendance Log")
        verbose_name_plural = _("Face Recognition Attendance Logs")
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.employee_id} - {self.action} - {self.timestamp}"


@receiver(post_delete, sender=EmployeeFaceDetection)
def delete_image_file(sender, instance, **kwargs):
    if instance.image and instance.image.path:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(post_delete, sender=FaceRecognitionAttendanceLog)
def delete_captured_image_file(sender, instance, **kwargs):
    if instance.captured_image and instance.captured_image.path:
        if os.path.isfile(instance.captured_image.path):
            os.remove(instance.captured_image.path)
