import datetime
import sys

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings

from base.backends import logger


def create_work_record():
    from attendance.models import WorkRecords, Attendance
    from employee.models import Employee
    from attendance.methods.utils import monthly_leave_days

    date = datetime.datetime.today()
    work_records = WorkRecords.objects.filter(date=date).values_list(
        "employee_id", flat=True
    )
    employees = Employee.objects.exclude(id__in=work_records)
    records_to_create = []
    
    # Get leave dates for the current month
    leave_dates = monthly_leave_days(date.month, date.year)

    for employee in employees:
        try:
            shift_schedule = employee.get_shift_schedule()
            if shift_schedule is None:
                continue

            shift = employee.get_shift()
            
            # Check if employee has attendance for this date
            has_attendance = Attendance.objects.filter(
                employee_id=employee,
                attendance_date=date
            ).exists()
            
            # Check if it's a holiday/leave day
            is_holiday = date in leave_dates
            
            # Determine work record type
            if is_holiday:
                work_record_type = "HD"  # Holiday/Company Leave
                message = "Holiday/Company Leave"
            elif has_attendance:
                # If attendance exists, let the signal handle it
                continue
            else:
                work_record_type = "ABS"  # Absent
                message = "Absent"
            
            record = WorkRecords(
                employee_id=employee,
                date=date,
                work_record_type=work_record_type,
                shift_id=shift,
                message=message,
            )
            records_to_create.append(record)
        except Exception as e:
            logger.error(f"Error preparing work record for {employee}: {e}")

    if records_to_create:
        try:
            WorkRecords.objects.bulk_create(records_to_create)
            print(f"Created {len(records_to_create)} work records for {date}.")
        except Exception as e:
            logger.error(f"Failed to bulk create work records: {e}")
    else:
        print(f"No new work records to create for {date}.")


if not any(
    cmd in sys.argv
    for cmd in ["makemigrations", "migrate", "compilemessages", "flush", "shell"]
):
    """
    Initializes and starts background tasks using APScheduler when the server is running.
    """
    scheduler = BackgroundScheduler(timezone=pytz.timezone(settings.TIME_ZONE))

    scheduler.add_job(
        create_work_record, "interval", minutes=30, misfire_grace_time=3600 * 3
    )
    scheduler.add_job(
        create_work_record,
        "cron",
        hour=0,
        minute=30,
        misfire_grace_time=3600 * 9,
        id="create_daily_work_record",
        replace_existing=True,
    )

    scheduler.start()
