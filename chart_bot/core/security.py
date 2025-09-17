"""
Security and Permission Management for Chart Bot
"""
from typing import Dict, Any, List, Optional
from django.contrib.auth.models import User
from django.db.models import Q
from employee.models import Employee, EmployeeWorkInformation
from base.models import Company
import logging

logger = logging.getLogger(__name__)


class SecurityManager:
    """
    Manages security and permissions for Chart Bot
    """
    
    def __init__(self, user: User):
        self.user = user
        self.employee = getattr(user, 'employee_get', None)
        self.user_role = self._determine_user_role()
    
    def _determine_user_role(self) -> str:
        """
        Determine user role based on permissions and relationships
        """
        if not self.employee:
            return "guest"
        
        # Check if user is admin (has admin permissions)
        if self.user.is_superuser or self.user.is_staff:
            return "admin"
        
        # Check if user is HR manager (manages other employees)
        if self._is_hr_manager():
            return "hr_manager"
        
        # Default to employee
        return "employee"
    
    def _is_hr_manager(self) -> bool:
        """
        Check if user is an HR manager (has subordinates)
        """
        if not self.employee:
            return False
        
        # Check if user has subordinates
        has_subordinates = EmployeeWorkInformation.objects.filter(
            reporting_manager_id=self.employee
        ).exists()
        
        # Check for specific HR permissions
        has_hr_permissions = (
            self.user.has_perm('employee.view_all_employees') or
            self.user.has_perm('employee.manage_department') or
            self.user.has_perm('attendance.change_validateattendance') or
            self.user.has_perm('leave.change_leaverequest')
        )
        
        return has_subordinates or has_hr_permissions
    
    def get_accessible_employees(self) -> List[int]:
        """
        Get list of employee IDs that the user can access
        """
        if self.user_role == "admin":
            # Admin can access all employees
            return list(Employee.objects.filter(is_active=True).values_list('id', flat=True))
        
        elif self.user_role == "hr_manager":
            # HR manager can access themselves and their subordinates
            subordinate_ids = list(EmployeeWorkInformation.objects.filter(
                reporting_manager_id=self.employee
            ).values_list('employee_id', flat=True))
            
            # Include themselves
            if self.employee:
                subordinate_ids.append(self.employee.id)
            
            return subordinate_ids
        
        elif self.user_role == "employee":
            # Employee can only access themselves
            return [self.employee.id] if self.employee else []
        
        return []
    
    def can_access_employee_data(self, employee_id: int) -> bool:
        """
        Check if user can access specific employee data
        """
        accessible_employees = self.get_accessible_employees()
        return employee_id in accessible_employees
    
    def can_access_company_data(self) -> bool:
        """
        Check if user can access company-wide data
        """
        return self.user_role == "admin"
    
    def can_access_payroll_data(self, employee_id: Optional[int] = None) -> bool:
        """
        Check if user can access payroll data
        """
        if self.user_role == "admin":
            return True
        
        if self.user_role == "hr_manager" and employee_id:
            return self.can_access_employee_data(employee_id)
        
        if self.user_role == "employee" and employee_id:
            return employee_id == self.employee.id if self.employee else False
        
        return False
    
    def can_access_attendance_data(self, employee_id: Optional[int] = None) -> bool:
        """
        Check if user can access attendance data
        """
        if self.user_role == "admin":
            return True
        
        if self.user_role == "hr_manager" and employee_id:
            return self.can_access_employee_data(employee_id)
        
        if self.user_role == "employee" and employee_id:
            return employee_id == self.employee.id if self.employee else False
        
        return False
    
    def can_access_leave_data(self, employee_id: Optional[int] = None) -> bool:
        """
        Check if user can access leave data
        """
        if self.user_role == "admin":
            return True
        
        if self.user_role == "hr_manager" and employee_id:
            return self.can_access_employee_data(employee_id)
        
        if self.user_role == "employee" and employee_id:
            return employee_id == self.employee.id if self.employee else False
        
        return False
    
    def get_security_context(self) -> Dict[str, Any]:
        """
        Get security context for the user
        """
        return {
            "user_role": self.user_role,
            "user_id": self.user.id,
            "employee_id": self.employee.id if self.employee else None,
            "accessible_employees": self.get_accessible_employees(),
            "can_access_company_data": self.can_access_company_data(),
            "permissions": {
                "payroll": self.can_access_payroll_data(),
                "attendance": self.can_access_attendance_data(),
                "leave": self.can_access_leave_data(),
            }
        }
    
    def validate_query_permissions(self, query_type: str, target_employee_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate if user has permissions for specific query type
        """
        validation_result = {
            "allowed": False,
            "reason": "",
            "suggested_action": ""
        }
        
        if query_type == "personal_data":
            if target_employee_id and not self.can_access_employee_data(target_employee_id):
                validation_result["reason"] = "You don't have permission to view this employee's data."
                validation_result["suggested_action"] = "You can only view your own data."
            else:
                validation_result["allowed"] = True
        
        elif query_type == "company_data":
            if not self.can_access_company_data():
                validation_result["reason"] = "You don't have permission to view company-wide data."
                validation_result["suggested_action"] = "Contact your administrator for access."
            else:
                validation_result["allowed"] = True
        
        elif query_type == "team_data":
            if self.user_role not in ["hr_manager", "admin"]:
                validation_result["reason"] = "You don't have permission to view team data."
                validation_result["suggested_action"] = "Only managers can view team information."
            else:
                validation_result["allowed"] = True
        
        elif query_type == "payroll":
            if not self.can_access_payroll_data(target_employee_id):
                validation_result["reason"] = "You don't have permission to view payroll information."
                validation_result["suggested_action"] = "You can only view your own payroll details."
            else:
                validation_result["allowed"] = True
        
        elif query_type == "attendance":
            if not self.can_access_attendance_data(target_employee_id):
                validation_result["reason"] = "You don't have permission to view attendance information."
                validation_result["suggested_action"] = "You can only view your own attendance records."
            else:
                validation_result["allowed"] = True
        
        elif query_type == "leave":
            if not self.can_access_leave_data(target_employee_id):
                validation_result["reason"] = "You don't have permission to view leave information."
                validation_result["suggested_action"] = "You can only view your own leave records."
            else:
                validation_result["allowed"] = True
        
        return validation_result
