"""
Enhanced Query Analyzer - Understands specific HR queries
"""
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date

logger = logging.getLogger(__name__)


class EnhancedQueryAnalyzer:
    """
    Enhanced query analyzer that understands specific HR queries
    """
    
    def __init__(self):
        self.personal_keywords = [
            'my', 'mine', 'myself', 'i', 'me', 'personal', 'own'
        ]
        
        self.attendance_keywords = [
            'attendance', 'present', 'absent', 'check in', 'check out', 'clock in', 'clock out',
            'punch', 'time', 'hours', 'overtime', 'late', 'early'
        ]
        
        self.leave_keywords = [
            'leave', 'vacation', 'sick', 'holiday', 'time off', 'absence', 'balance',
            'remaining', 'used', 'allocated', 'request', 'approve'
        ]
        
        self.payroll_keywords = [
            'salary', 'payroll', 'payslip', 'wage', 'income', 'earnings', 'deduction',
            'allowance', 'bonus', 'increment', 'payment'
        ]
        
        self.profile_keywords = [
            'profile', 'information', 'details', 'email', 'phone', 'address', 'contact',
            'name', 'department', 'position', 'manager', 'employee id'
        ]
        
        self.team_keywords = [
            'team', 'subordinates', 'staff', 'employees', 'members', 'reports'
        ]
        
        self.company_keywords = [
            'company', 'organization', 'all employees', 'everyone', 'total', 'statistics'
        ]
        
        logger.info("Enhanced Query Analyzer initialized")
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze the user query and extract intent and parameters
        """
        try:
            query_lower = query.lower().strip()
            
            # Determine query type
            query_type = self._determine_query_type(query_lower)
            
            # Extract parameters
            parameters = self._extract_parameters(query_lower, query_type)
            
            # Determine if it requires data
            requires_data = self._requires_data(query_type)
            
            # Determine user scope
            user_scope = self._determine_user_scope(query_lower)
            
            analysis = {
                'query_type': query_type,
                'parameters': parameters,
                'requires_data': requires_data,
                'user_scope': user_scope,
                'original_query': query,
                'confidence': self._calculate_confidence(query_lower, query_type)
            }
            
            logger.info(f"Query analysis: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            return {
                'query_type': 'unknown',
                'parameters': {},
                'requires_data': False,
                'user_scope': 'personal',
                'original_query': query,
                'confidence': 0.0
            }
    
    def _determine_query_type(self, query_lower: str) -> str:
        """
        Determine the type of query
        """
        # Check for specific patterns first
        if any(keyword in query_lower for keyword in ['email', 'mail', 'contact']):
            return 'email_query'
        
        if any(keyword in query_lower for keyword in ['phone', 'mobile', 'number']):
            return 'phone_query'
        
        if any(keyword in query_lower for keyword in ['employee id', 'emp id', 'id number']):
            return 'employee_id_query'
        
        if any(keyword in query_lower for keyword in ['attendance', 'present', 'absent']):
            return 'attendance_query'
        
        if any(keyword in query_lower for keyword in ['leave', 'vacation', 'balance']):
            return 'leave_query'
        
        if any(keyword in query_lower for keyword in ['salary', 'payroll', 'payslip']):
            return 'payroll_query'
        
        if any(keyword in query_lower for keyword in ['profile', 'information', 'details']):
            return 'profile_query'
        
        if any(keyword in query_lower for keyword in ['team', 'subordinates', 'staff']):
            return 'team_query'
        
        if any(keyword in query_lower for keyword in ['company', 'organization', 'all employees']):
            return 'company_query'
        
        # General queries
        if any(keyword in query_lower for keyword in ['help', 'what can you do', 'capabilities']):
            return 'help_query'
        
        if any(keyword in query_lower for keyword in ['hello', 'hi', 'greeting']):
            return 'greeting_query'
        
        return 'general_query'
    
    def _extract_parameters(self, query_lower: str, query_type: str) -> Dict[str, Any]:
        """
        Extract parameters from the query
        """
        parameters = {}
        
        # Extract time periods
        if 'today' in query_lower:
            parameters['time_period'] = 'today'
        elif 'yesterday' in query_lower:
            parameters['time_period'] = 'yesterday'
        elif 'this week' in query_lower:
            parameters['time_period'] = 'this_week'
        elif 'this month' in query_lower:
            parameters['time_period'] = 'this_month'
        elif 'last month' in query_lower:
            parameters['time_period'] = 'last_month'
        elif 'this year' in query_lower:
            parameters['time_period'] = 'this_year'
        
        # Extract specific dates
        date_pattern = r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})'
        date_match = re.search(date_pattern, query_lower)
        if date_match:
            day, month, year = date_match.groups()
            if len(year) == 2:
                year = '20' + year
            parameters['specific_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Extract month names
        month_names = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        for month_name, month_num in month_names.items():
            if month_name in query_lower:
                parameters['month'] = month_num
                break
        
        # Extract year
        year_pattern = r'(20\d{2})'
        year_match = re.search(year_pattern, query_lower)
        if year_match:
            parameters['year'] = int(year_match.group(1))
        
        # Extract leave types
        leave_types = ['sick', 'casual', 'annual', 'maternity', 'paternity', 'emergency']
        for leave_type in leave_types:
            if leave_type in query_lower:
                parameters['leave_type'] = leave_type
                break
        
        return parameters
    
    def _requires_data(self, query_type: str) -> bool:
        """
        Determine if the query requires database data
        """
        data_required_types = [
            'email_query', 'phone_query', 'employee_id_query',
            'attendance_query', 'leave_query', 'payroll_query',
            'profile_query', 'team_query', 'company_query'
        ]
        return query_type in data_required_types
    
    def _determine_user_scope(self, query_lower: str) -> str:
        """
        Determine the scope of the query (personal, team, company)
        """
        if any(keyword in query_lower for keyword in self.personal_keywords):
            return 'personal'
        elif any(keyword in query_lower for keyword in self.team_keywords):
            return 'team'
        elif any(keyword in query_lower for keyword in self.company_keywords):
            return 'company'
        else:
            return 'personal'  # Default to personal
    
    def _calculate_confidence(self, query_lower: str, query_type: str) -> float:
        """
        Calculate confidence score for the analysis
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on keyword matches
        if query_type == 'email_query' and any(keyword in query_lower for keyword in ['email', 'mail']):
            confidence += 0.3
        
        if query_type == 'attendance_query' and any(keyword in query_lower for keyword in self.attendance_keywords):
            confidence += 0.3
        
        if query_type == 'leave_query' and any(keyword in query_lower for keyword in self.leave_keywords):
            confidence += 0.3
        
        if query_type == 'payroll_query' and any(keyword in query_lower for keyword in self.payroll_keywords):
            confidence += 0.3
        
        if query_type == 'profile_query' and any(keyword in query_lower for keyword in self.profile_keywords):
            confidence += 0.3
        
        return min(confidence, 1.0)
