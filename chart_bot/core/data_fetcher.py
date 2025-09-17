"""
Data Fetcher for Chart Bot
Handles database queries and data retrieval
"""
from typing import Dict, Any, List, Optional
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, date, timedelta
from employee.models import Employee, EmployeeWorkInformation
from attendance.models import Attendance, AttendanceActivity, AttendanceOverTime
from leave.models import LeaveRequest, LeaveType
from payroll.models.models import Contract, Allowance, Deduction
from base.models import Company, Department, JobPosition
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Handles data fetching for Chart Bot queries
    """
    
    def __init__(self, security_manager):
        self.security_manager = security_manager
        self.accessible_employees = security_manager.get_accessible_employees()
    
    def get_employee_profile(self, employee_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get employee profile information
        """
        if not employee_id:
            employee_id = self.security_manager.employee.id if self.security_manager.employee else None
        
        if not self.security_manager.can_access_employee_data(employee_id):
            return {"error": "Access denied"}
        
        try:
            employee = Employee.objects.get(id=employee_id)
            work_info = getattr(employee, 'employee_work_info', None)
            
            profile_data = {
                "id": employee.id,
                "name": employee.get_full_name(),
                "email": employee.email,
                "phone": employee.phone,
                "department": work_info.department_id.department if work_info and work_info.department_id else None,
                "job_position": work_info.job_position_id.job_position if work_info and work_info.job_position_id else None,
                "reporting_manager": work_info.reporting_manager_id.get_full_name() if work_info and work_info.reporting_manager_id else None,
                "joining_date": work_info.date_joining if work_info else None,
                "is_active": employee.is_active
            }
            
            return profile_data
        except Employee.DoesNotExist:
            return {"error": "Employee not found"}
    
    def get_attendance_data(self, employee_id: Optional[int] = None, 
                          start_date: Optional[date] = None, 
                          end_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get attendance data for employee(s)
        """
        if not start_date:
            start_date = date.today().replace(day=1)  # First day of current month
        if not end_date:
            end_date = date.today()
        
        if employee_id and not self.security_manager.can_access_attendance_data(employee_id):
            return {"error": "Access denied"}
        
        try:
            if employee_id:
                # Single employee attendance
                attendances = Attendance.objects.filter(
                    employee_id=employee_id,
                    attendance_date__range=[start_date, end_date]
                ).order_by('-attendance_date')
                
                attendance_data = []
                total_worked_hours = 0
                total_overtime = 0
                
                for attendance in attendances:
                    attendance_data.append({
                        "date": attendance.attendance_date,
                        "check_in": attendance.attendance_clock_in,
                        "check_out": attendance.attendance_clock_out,
                        "worked_hours": attendance.attendance_worked_hour,
                        "overtime": attendance.attendance_overtime,
                        "status": "Present" if attendance.attendance_clock_in else "Absent"
                    })
                    
                    # Calculate totals
                    if attendance.attendance_worked_hour:
                        hours, minutes = map(int, attendance.attendance_worked_hour.split(':'))
                        total_worked_hours += hours + (minutes / 60)
                    
                    if attendance.attendance_overtime:
                        hours, minutes = map(int, attendance.attendance_overtime.split(':'))
                        total_overtime += hours + (minutes / 60)
                
                return {
                    "employee_id": employee_id,
                    "period": f"{start_date} to {end_date}",
                    "attendances": attendance_data,
                    "summary": {
                        "total_days": len(attendance_data),
                        "present_days": len([a for a in attendance_data if a["status"] == "Present"]),
                        "total_worked_hours": round(total_worked_hours, 2),
                        "total_overtime": round(total_overtime, 2)
                    }
                }
            else:
                # Team attendance (for HR managers)
                if self.security_manager.user_role not in ["hr_manager", "admin"]:
                    return {"error": "Access denied"}
                
                team_attendances = Attendance.objects.filter(
                    employee_id__in=self.accessible_employees,
                    attendance_date__range=[start_date, end_date]
                ).select_related('employee_id')
                
                team_data = {}
                for attendance in team_attendances:
                    emp_id = attendance.employee_id.id
                    if emp_id not in team_data:
                        team_data[emp_id] = {
                            "employee_name": attendance.employee_id.get_full_name(),
                            "attendances": [],
                            "total_days": 0,
                            "present_days": 0
                        }
                    
                    team_data[emp_id]["attendances"].append({
                        "date": attendance.attendance_date,
                        "worked_hours": attendance.attendance_worked_hour,
                        "status": "Present" if attendance.attendance_clock_in else "Absent"
                    })
                    
                    team_data[emp_id]["total_days"] += 1
                    if attendance.attendance_clock_in:
                        team_data[emp_id]["present_days"] += 1
                
                return {
                    "period": f"{start_date} to {end_date}",
                    "team_data": team_data
                }
                
        except Exception as e:
            logger.error(f"Error fetching attendance data: {str(e)}")
            return {"error": "Failed to fetch attendance data"}
    
    def get_leave_data(self, employee_id: Optional[int] = None,
                      start_date: Optional[date] = None,
                      end_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get leave data for employee(s)
        """
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()
        
        if employee_id and not self.security_manager.can_access_leave_data(employee_id):
            return {"error": "Access denied"}
        
        try:
            if employee_id:
                # Single employee leave data
                leave_requests = LeaveRequest.objects.filter(
                    employee_id=employee_id,
                    start_date__lte=end_date,
                    end_date__gte=start_date
                ).select_related('leave_type_id')
                
                leave_data = []
                for leave in leave_requests:
                    leave_data.append({
                        "leave_type": leave.leave_type_id.name,
                        "start_date": leave.start_date,
                        "end_date": leave.end_date,
                        "requested_days": leave.requested_days,
                        "status": leave.status,
                        "description": leave.description
                    })
                
                # Get leave balance
                leave_balance = {}
                leave_types = LeaveType.objects.all()
                for leave_type in leave_types:
                    balance = leave_type.get_available_leaves(employee_id)
                    leave_balance[leave_type.name] = balance
                
                return {
                    "employee_id": employee_id,
                    "period": f"{start_date} to {end_date}",
                    "leave_requests": leave_data,
                    "leave_balance": leave_balance
                }
            else:
                # Team leave data
                if self.security_manager.user_role not in ["hr_manager", "admin"]:
                    return {"error": "Access denied"}
                
                team_leaves = LeaveRequest.objects.filter(
                    employee_id__in=self.accessible_employees,
                    start_date__lte=end_date,
                    end_date__gte=start_date
                ).select_related('employee_id', 'leave_type_id')
                
                team_data = {}
                for leave in team_leaves:
                    emp_id = leave.employee_id.id
                    if emp_id not in team_data:
                        team_data[emp_id] = {
                            "employee_name": leave.employee_id.get_full_name(),
                            "leaves": []
                        }
                    
                    team_data[emp_id]["leaves"].append({
                        "leave_type": leave.leave_type_id.name,
                        "start_date": leave.start_date,
                        "end_date": leave.end_date,
                        "requested_days": leave.requested_days,
                        "status": leave.status
                    })
                
                return {
                    "period": f"{start_date} to {end_date}",
                    "team_data": team_data
                }
                
        except Exception as e:
            logger.error(f"Error fetching leave data: {str(e)}")
            return {"error": "Failed to fetch leave data"}
    
    def get_payroll_data(self, employee_id: Optional[int] = None,
                        month: Optional[str] = None,
                        year: Optional[int] = None) -> Dict[str, Any]:
        """
        Get payroll data for employee(s)
        """
        if not month:
            month = datetime.now().strftime("%B").lower()
        if not year:
            year = datetime.now().year
        
        if employee_id and not self.security_manager.can_access_payroll_data(employee_id):
            return {"error": "Access denied"}
        
        try:
            if employee_id:
                # Single employee payroll
                employee = Employee.objects.get(id=employee_id)
                work_info = getattr(employee, 'employee_work_info', None)
                
                payroll_data = {
                    "employee_id": employee_id,
                    "employee_name": employee.get_full_name(),
                    "month": month,
                    "year": year,
                    "basic_salary": work_info.basic_salary if work_info else 0,
                    "salary_per_hour": work_info.salary_hour if work_info else 0
                }
                
                # Get allowances and deductions
                allowances = Allowance.objects.filter(
                    employee_id=employee_id,
                    month=month,
                    year=year
                )
                
                deductions = Deduction.objects.filter(
                    employee_id=employee_id,
                    month=month,
                    year=year
                )
                
                payroll_data["allowances"] = [
                    {"name": allowance.allowance_type_id.title, "amount": allowance.amount}
                    for allowance in allowances
                ]
                
                payroll_data["deductions"] = [
                    {"name": deduction.deduction_type_id.title, "amount": deduction.amount}
                    for deduction in deductions
                ]
                
                # Calculate totals
                total_allowances = sum(a.amount for a in allowances)
                total_deductions = sum(d.amount for d in deductions)
                net_salary = payroll_data["basic_salary"] + total_allowances - total_deductions
                
                payroll_data["summary"] = {
                    "basic_salary": payroll_data["basic_salary"],
                    "total_allowances": total_allowances,
                    "total_deductions": total_deductions,
                    "net_salary": net_salary
                }
                
                return payroll_data
            else:
                # Team payroll (admin only)
                if self.security_manager.user_role != "admin":
                    return {"error": "Access denied"}
                
                team_payroll = []
                for emp_id in self.accessible_employees:
                    employee = Employee.objects.get(id=emp_id)
                    work_info = getattr(employee, 'employee_work_info', None)
                    
                    if work_info:
                        team_payroll.append({
                            "employee_id": emp_id,
                            "employee_name": employee.get_full_name(),
                            "basic_salary": work_info.basic_salary or 0
                        })
                
                return {
                    "month": month,
                    "year": year,
                    "team_payroll": team_payroll
                }
                
        except Exception as e:
            logger.error(f"Error fetching payroll data: {str(e)}")
            return {"error": "Failed to fetch payroll data"}
    
    def get_company_statistics(self) -> Dict[str, Any]:
        """
        Get company-wide statistics (admin only)
        """
        if not self.security_manager.can_access_company_data():
            return {"error": "Access denied"}
        
        try:
            stats = {
                "total_employees": Employee.objects.filter(is_active=True).count(),
                "total_departments": Department.objects.count(),
                "total_job_positions": JobPosition.objects.count(),
                "departments": []
            }
            
            # Department-wise employee count
            departments = Department.objects.all()
            for dept in departments:
                emp_count = EmployeeWorkInformation.objects.filter(
                    department_id=dept
                ).count()
                stats["departments"].append({
                    "name": dept.department,
                    "employee_count": emp_count
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching company statistics: {str(e)}")
            return {"error": "Failed to fetch company statistics"}
