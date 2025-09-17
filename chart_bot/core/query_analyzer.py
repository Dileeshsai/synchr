"""
Query Analyzer for Chart Bot
Analyzes user queries and determines intent and required data
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """
    Analyzes user queries to determine intent and extract parameters
    """
    
    def __init__(self):
        self.intent_patterns = {
            'attendance': [
                r'attendance', r'check.*in', r'check.*out', r'present', r'absent',
                r'worked.*hours', r'overtime', r'time.*tracking'
            ],
            'leave': [
                r'leave', r'vacation', r'sick.*leave', r'holiday', r'balance',
                r'request.*leave', r'approved.*leave', r'pending.*leave'
            ],
            'payroll': [
                r'salary', r'payroll', r'wage', r'income', r'payment',
                r'allowance', r'deduction', r'net.*salary', r'gross.*salary'
            ],
            'profile': [
                r'profile', r'personal.*info', r'contact', r'department',
                r'position', r'manager', r'joining.*date'
            ],
            'team': [
                r'team', r'subordinates', r'my.*team', r'team.*members',
                r'team.*attendance', r'team.*leave'
            ],
            'company': [
                r'company', r'organization', r'departments', r'statistics',
                r'overview', r'all.*employees'
            ]
        }
        
        self.time_patterns = {
            'today': r'today',
            'yesterday': r'yesterday',
            'this_week': r'this.*week',
            'last_week': r'last.*week',
            'this_month': r'this.*month',
            'last_month': r'last.*month',
            'this_year': r'this.*year',
            'last_year': r'last.*year'
        }
        
        self.employee_patterns = [
            r'my', r'me', r'myself', r'own'
        ]
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze user query and return structured intent
        """
        query_lower = query.lower().strip()
        
        analysis = {
            'original_query': query,
            'intent': self._detect_intent(query_lower),
            'time_period': self._extract_time_period(query_lower),
            'target_employee': self._extract_target_employee(query_lower),
            'parameters': self._extract_parameters(query_lower),
            'confidence': 0.0
        }
        
        # Calculate confidence based on pattern matches
        analysis['confidence'] = self._calculate_confidence(analysis)
        
        return analysis
    
    def _detect_intent(self, query: str) -> str:
        """
        Detect the primary intent of the query
        """
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query):
                    score += 1
            intent_scores[intent] = score
        
        # Return intent with highest score
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        
        return 'general'
    
    def _extract_time_period(self, query: str) -> Dict[str, Any]:
        """
        Extract time period from query
        """
        time_period = {
            'type': 'custom',
            'start_date': None,
            'end_date': None,
            'month': None,
            'year': None
        }
        
        # Check for specific time patterns
        for period_type, pattern in self.time_patterns.items():
            if re.search(pattern, query):
                time_period['type'] = period_type
                break
        
        # Extract specific dates
        date_pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})'
        date_matches = re.findall(date_pattern, query)
        if date_matches:
            # Use first date match
            day, month, year = date_matches[0]
            if len(year) == 2:
                year = '20' + year
            time_period['start_date'] = date(int(year), int(month), int(day))
            time_period['type'] = 'specific_date'
        
        # Extract month and year
        month_pattern = r'(january|february|march|april|may|june|july|august|september|october|november|december)'
        month_match = re.search(month_pattern, query)
        if month_match:
            month_name = month_match.group(1)
            month_num = datetime.strptime(month_name, '%B').month
            time_period['month'] = month_num
        
        year_pattern = r'(20\d{2})'
        year_match = re.search(year_pattern, query)
        if year_match:
            time_period['year'] = int(year_match.group(1))
        
        # Set default time period if none specified
        if time_period['type'] == 'custom':
            time_period['type'] = 'this_month'
        
        return time_period
    
    def _extract_target_employee(self, query: str) -> Optional[int]:
        """
        Extract target employee from query
        """
        # Check if query is about self
        for pattern in self.employee_patterns:
            if re.search(pattern, query):
                return 'self'
        
        # Check for specific employee names (this would need employee name mapping)
        # For now, return None for other employees
        return None
    
    def _extract_parameters(self, query: str) -> Dict[str, Any]:
        """
        Extract additional parameters from query
        """
        parameters = {}
        
        # Extract numbers
        numbers = re.findall(r'\d+', query)
        if numbers:
            parameters['numbers'] = [int(n) for n in numbers]
        
        # Extract specific keywords
        if 'export' in query or 'download' in query:
            parameters['export'] = True
        
        if 'report' in query:
            parameters['report'] = True
        
        if 'summary' in query:
            parameters['summary'] = True
        
        return parameters
    
    def _calculate_confidence(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the analysis
        """
        confidence = 0.0
        
        # Base confidence for intent detection
        if analysis['intent'] != 'general':
            confidence += 0.4
        
        # Confidence for time period detection
        if analysis['time_period']['type'] != 'custom':
            confidence += 0.3
        
        # Confidence for parameter extraction
        if analysis['parameters']:
            confidence += 0.2
        
        # Confidence for target employee detection
        if analysis['target_employee'] is not None:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_required_permissions(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Get required permissions for the query
        """
        permissions = []
        
        intent = analysis['intent']
        target_employee = analysis['target_employee']
        
        if intent == 'attendance':
            permissions.append('attendance')
        elif intent == 'leave':
            permissions.append('leave')
        elif intent == 'payroll':
            permissions.append('payroll')
        elif intent == 'profile':
            permissions.append('personal_data')
        elif intent == 'team':
            permissions.append('team_data')
        elif intent == 'company':
            permissions.append('company_data')
        
        return permissions
    
    def get_data_requirements(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get data requirements for the query
        """
        requirements = {
            'data_type': analysis['intent'],
            'employee_id': analysis['target_employee'],
            'time_period': analysis['time_period'],
            'additional_params': analysis['parameters']
        }
        
        return requirements
