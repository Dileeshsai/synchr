"""
Enhanced Data Fetcher - Real HRMS Database Integration
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from django.contrib.auth.models import User
from django.db.models import Q, Sum, Count, Avg

logger = logging.getLogger(__name__)


class EnhancedDataFetcher:
    """
    Enhanced data fetcher that connects to real HRMS database
    """
    
    def __init__(self, user: User):
        self.user = user
        self.employee = self._get_employee()
        logger.info(f"Enhanced Data Fetcher initialized for user: {user.username}")
    
    def _get_employee(self):
        """
        Get employee record for the user
        """
        try:
            if hasattr(self.user, 'employee_get'):
                return self.user.employee_get
            return None
        except Exception as e:
            logger.warning(f"Could not get employee record: {str(e)}")
            return None
    
    def get_personal_info(self) -> Dict[str, Any]:
        """
        Get personal information for the user
        """
        try:
            if not self.employee:
                return {"error": "No employee record found"}
            
            info = {
                "employee_id": self.employee.id,
                "employee_id_number": getattr(self.employee, 'badge_id', 'N/A'),
                "full_name": self.employee.get_full_name(),
                "first_name": getattr(self.employee, 'employee_first_name', 'N/A'),
                "last_name": getattr(self.employee, 'employee_last_name', 'N/A'),
                "email": getattr(self.employee, 'email', 'N/A'),
                "phone": getattr(self.employee, 'phone', 'N/A'),
                "date_of_birth": getattr(self.employee, 'dob', 'N/A'),
                "gender": getattr(self.employee, 'gender', 'N/A'),
                "is_active": self.employee.is_active,
                "date_joined": getattr(self.employee, 'date_joined', 'N/A'),
            }
            
            # Get work information
            try:
                from employee.models import EmployeeWorkInformation
                work_info = EmployeeWorkInformation.objects.filter(employee_id=self.employee).first()
                if work_info:
                    info.update({
                        "department": getattr(work_info.department_id, 'department', 'N/A') if work_info.department_id else 'N/A',
                        "job_position": getattr(work_info.job_position_id, 'job_position', 'N/A') if work_info.job_position_id else 'N/A',
                        "work_type": getattr(work_info.work_type_id, 'work_type', 'N/A') if work_info.work_type_id else 'N/A',
                        "shift": getattr(work_info.shift_id, 'shift', 'N/A') if work_info.shift_id else 'N/A',
                        "reporting_manager": getattr(work_info.reporting_manager_id, 'get_full_name', lambda: 'N/A')(),
                        "employee_type": getattr(work_info.employee_type_id, 'employee_type', 'N/A') if work_info.employee_type_id else 'N/A',
                        "basic_salary": getattr(work_info, 'basic_salary', 'N/A'),
                    })
            except Exception as e:
                logger.warning(f"Could not get work information: {str(e)}")
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting personal info: {str(e)}")
            return {"error": f"Could not retrieve personal information: {str(e)}"}
    
    def get_attendance_data(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get attendance data for the user
        """
        try:
            if not self.employee:
                return {"error": "No employee record found"}
            
            # Default to current month if no dates provided
            if not start_date:
                start_date = date.today().replace(day=1)
            if not end_date:
                end_date = date.today()
            
            from attendance.models import Attendance, AttendanceActivity
            
            # Get attendance records
            attendance_records = Attendance.objects.filter(
                employee_id=self.employee,
                attendance_date__range=[start_date, end_date]
            ).order_by('-attendance_date')
            
            # Calculate statistics
            total_days = (end_date - start_date).days + 1
            present_days = attendance_records.filter(attendance_validated=True).count()
            absent_days = total_days - present_days
            
            # Get recent attendance
            recent_attendance = []
            for record in attendance_records[:10]:  # Last 10 records
                recent_attendance.append({
                    "date": record.attendance_date.strftime("%Y-%m-%d"),
                    "check_in": record.attendance_clock_in.strftime("%H:%M") if record.attendance_clock_in else "N/A",
                    "check_out": record.attendance_clock_out.strftime("%H:%M") if record.attendance_clock_out else "N/A",
                    "status": "Present" if record.attendance_validated else "Absent",
                    "overtime_hours": getattr(record, 'overtime_hour', 0),
                })
            
            return {
                "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "total_days": total_days,
                "present_days": present_days,
                "absent_days": absent_days,
                "attendance_percentage": round((present_days / total_days) * 100, 2) if total_days > 0 else 0,
                "recent_attendance": recent_attendance,
            }
            
        except Exception as e:
            logger.error(f"Error getting attendance data: {str(e)}")
            return {"error": f"Could not retrieve attendance data: {str(e)}"}
    
    def get_leave_data(self) -> Dict[str, Any]:
        """
        Get leave data for the user
        """
        try:
            if not self.employee:
                return {"error": "No employee record found"}
            
            from leave.models import LeaveRequest, LeaveAllocation
            
            # Get leave allocations
            allocations = LeaveAllocation.objects.filter(employee_id=self.employee)
            leave_balance = {}
            
            for allocation in allocations:
                leave_type = getattr(allocation.leave_type, 'name', 'Unknown')
                leave_balance[leave_type] = {
                    "allocated": getattr(allocation, 'allocated_days', 0),
                    "used": getattr(allocation, 'used_days', 0),
                    "remaining": getattr(allocation, 'remaining_days', 0),
                }
            
            # Get recent leave requests
            recent_requests = LeaveRequest.objects.filter(
                employee_id=self.employee
            ).order_by('-created_at')[:5]
            
            recent_leave_requests = []
            for request in recent_requests:
                recent_leave_requests.append({
                    "leave_type": getattr(request.leave_type, 'name', 'Unknown'),
                    "start_date": request.start_date.strftime("%Y-%m-%d"),
                    "end_date": request.end_date.strftime("%Y-%m-%d"),
                    "days": request.days,
                    "status": getattr(request, 'status', 'Pending'),
                    "reason": getattr(request, 'description', 'N/A'),
                    "applied_date": request.created_at.strftime("%Y-%m-%d"),
                })
            
            return {
                "leave_balance": leave_balance,
                "recent_requests": recent_leave_requests,
            }
            
        except Exception as e:
            logger.error(f"Error getting leave data: {str(e)}")
            return {"error": f"Could not retrieve leave data: {str(e)}"}
    
    def get_payroll_data(self, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get payroll data for the user
        """
        try:
            if not self.employee:
                return {"error": "No employee record found"}
            
            # Default to current month/year
            if not month:
                month = date.today().month
            if not year:
                year = date.today().year
            
            from payroll.models.models import Payslip
            
            # Get payslip for the specified month/year
            payslip = Payslip.objects.filter(
                employee_id=self.employee,
                month=month,
                year=year
            ).first()
            
            if not payslip:
                return {
                    "error": f"No payslip found for {month}/{year}",
                    "month": month,
                    "year": year
                }
            
            # Get basic salary from work information
            basic_salary = 0
            try:
                from employee.models import EmployeeWorkInformation
                work_info = EmployeeWorkInformation.objects.filter(employee_id=self.employee).first()
                if work_info:
                    basic_salary = getattr(work_info, 'basic_salary', 0)
            except:
                pass
            
            return {
                "month": month,
                "year": year,
                "basic_salary": basic_salary,
                "gross_salary": getattr(payslip, 'gross_salary', 0),
                "net_salary": getattr(payslip, 'net_salary', 0),
                "total_deductions": getattr(payslip, 'total_deductions', 0),
                "total_allowances": getattr(payslip, 'total_allowances', 0),
                "status": getattr(payslip, 'status', 'Unknown'),
            }
            
        except Exception as e:
            logger.error(f"Error getting payroll data: {str(e)}")
            return {"error": f"Could not retrieve payroll data: {str(e)}"}
    
    def get_team_data(self) -> Dict[str, Any]:
        """
        Get team data for managers
        """
        try:
            if not self.employee:
                return {"error": "No employee record found"}
            
            from employee.models import EmployeeWorkInformation
            
            # Get subordinates
            subordinates = EmployeeWorkInformation.objects.filter(
                reporting_manager_id=self.employee
            ).select_related('employee_id')
            
            team_members = []
            for sub in subordinates:
                employee = sub.employee_id
                team_members.append({
                    "employee_id": employee.id,
                    "name": employee.get_full_name(),
                    "email": getattr(employee, 'email', 'N/A'),
                    "department": getattr(sub.department_id, 'department', 'N/A') if sub.department_id else 'N/A',
                    "job_position": getattr(sub.job_position_id, 'job_position', 'N/A') if sub.job_position_id else 'N/A',
                    "is_active": employee.is_active,
                })
            
            return {
                "team_size": len(team_members),
                "team_members": team_members,
            }
            
        except Exception as e:
            logger.error(f"Error getting team data: {str(e)}")
            return {"error": f"Could not retrieve team data: {str(e)}"}
    
    def get_company_data(self) -> Dict[str, Any]:
        """
        Get company-wide data for admins
        """
        try:
            from employee.models import Employee
            from attendance.models import Attendance
            from leave.models import LeaveRequest
            
            # Get company statistics
            total_employees = Employee.objects.filter(is_active=True).count()
            
            # Get today's attendance
            today = date.today()
            present_today = Attendance.objects.filter(
                attendance_date=today,
                attendance_validated=True
            ).count()
            
            # Get pending leave requests
            pending_leaves = LeaveRequest.objects.filter(
                status='requested'
            ).count()
            
            return {
                "total_employees": total_employees,
                "present_today": present_today,
                "absent_today": total_employees - present_today,
                "pending_leave_requests": pending_leaves,
                "attendance_percentage": round((present_today / total_employees) * 100, 2) if total_employees > 0 else 0,
            }
            
        except Exception as e:
            logger.error(f"Error getting company data: {str(e)}")
            return {"error": f"Could not retrieve company data: {str(e)}"}
