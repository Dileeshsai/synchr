"""
Management command to fix work records statuses
"""

from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from attendance.models import WorkRecords, Attendance
from attendance.methods.utils import monthly_leave_days


class Command(BaseCommand):
    help = 'Fix work records statuses for proper display'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to look back for fixing work records (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        start_date = date.today() - timedelta(days=days)
        end_date = date.today()
        
        self.stdout.write(f"Fixing work records from {start_date} to {end_date}")
        
        # Get all work records in the date range
        work_records = WorkRecords.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).select_related('employee_id', 'shift_id')
        
        fixed_count = 0
        
        for work_record in work_records:
            # Get leave dates for the month
            leave_dates = monthly_leave_days(work_record.date.month, work_record.date.year)
            
            # Check if employee has attendance for this date
            has_attendance = Attendance.objects.filter(
                employee_id=work_record.employee_id,
                attendance_date=work_record.date
            ).exists()
            
            # Check if it's a holiday/leave day
            is_holiday = work_record.date in leave_dates
            
            # Determine correct work record type
            if is_holiday:
                correct_type = "HD"  # Holiday/Company Leave
                correct_message = "Holiday/Company Leave"
            elif has_attendance:
                # If attendance exists, let the signal handle it
                continue
            elif work_record.work_record_type == "DFT" and work_record.shift_id and not is_holiday:
                correct_type = "ABS"  # Absent
                correct_message = "Absent"
            else:
                # Keep existing type if it's already correct
                continue
            
            if work_record.work_record_type != correct_type:
                if dry_run:
                    self.stdout.write(
                        f"Would change {work_record.employee_id} on {work_record.date} "
                        f"from {work_record.work_record_type} to {correct_type}"
                    )
                else:
                    work_record.work_record_type = correct_type
                    work_record.message = correct_message
                    work_record.save()
                    self.stdout.write(
                        f"Changed {work_record.employee_id} on {work_record.date} "
                        f"from {work_record.work_record_type} to {correct_type}"
                    )
                fixed_count += 1
        
        if dry_run:
            self.stdout.write(f"Would fix {fixed_count} work records")
        else:
            self.stdout.write(f"Fixed {fixed_count} work records")
