"""
Enhanced Chart Bot Agent - Real HRMS Data Integration
"""
import json
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
import requests

from .enhanced_data_fetcher import EnhancedDataFetcher
from .enhanced_query_analyzer import EnhancedQueryAnalyzer

logger = logging.getLogger(__name__)


class EnhancedChartBotAgent:
    """
    Enhanced Chart Bot Agent with real HRMS data integration
    """
    
    def __init__(self, user, session_id: str = None):
        self.user = user
        self.session_id = session_id or f"session_{user.id}_{datetime.now().timestamp()}"
        self.data_fetcher = EnhancedDataFetcher(user)
        self.query_analyzer = EnhancedQueryAnalyzer()
        self.llm_endpoint = "http://125.18.84.108:11434/api/generate"
        self.llm_model = "mistral"
        
        # Simple memory storage
        self.conversation_history = []
        self.max_history = 10
        
        logger.info(f"Enhanced Chart Bot Agent initialized for user: {user.username}")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query with real HRMS data
        """
        try:
            logger.info(f"Processing enhanced query: {query}")
            
            # Add to conversation history
            self.conversation_history.append({
                'type': 'user',
                'content': query,
                'timestamp': datetime.now().isoformat()
            })
            
            # Analyze query
            analysis = self.query_analyzer.analyze_query(query)
            logger.info(f"Query analysis: {analysis}")
            
            # Get user role
            user_role = self._get_user_role()
            
            # Check permissions
            if not self._check_permissions(analysis, user_role):
                response = "Sorry, you don't have permission to view this data."
                return self._create_response(False, response, "permission_denied")
            
            # Fetch real data if needed
            data = None
            if analysis.get('requires_data', False):
                data = self._fetch_real_data(analysis)
                logger.info(f"Real data fetched: {data}")
            
            # Generate response with real data
            response = self._generate_enhanced_response(query, analysis, data, user_role)
            
            # Add to conversation history
            self.conversation_history.append({
                'type': 'assistant',
                'content': response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Trim history
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            return self._create_response(True, response, "success", data)
            
        except Exception as e:
            logger.error(f"Error processing enhanced query: {str(e)}")
            return self._create_response(False, "Sorry, I encountered an error while processing your request.", "error")
    
    def _get_user_role(self) -> str:
        """
        Get user role
        """
        if self.user.is_superuser:
            return "admin"
        elif self.user.is_staff:
            return "hr_manager"
        else:
            return "employee"
    
    def _check_permissions(self, analysis: Dict[str, Any], user_role: str) -> bool:
        """
        Check permissions based on query type and user role
        """
        query_type = analysis.get('query_type', 'unknown')
        user_scope = analysis.get('user_scope', 'personal')
        
        # Admin can access everything
        if user_role == "admin":
            return True
        
        # HR manager can access team data
        if user_role == "hr_manager":
            return user_scope in ['personal', 'team']
        
        # Employee can only access personal data
        if user_role == "employee":
            return user_scope == 'personal'
        
        return False
    
    def _fetch_real_data(self, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch real data from HRMS database
        """
        try:
            query_type = analysis.get('query_type', 'unknown')
            parameters = analysis.get('parameters', {})
            
            if query_type in ['email_query', 'phone_query', 'employee_id_query', 'profile_query']:
                return self.data_fetcher.get_personal_info()
            
            elif query_type == 'attendance_query':
                return self.data_fetcher.get_attendance_data()
            
            elif query_type == 'leave_query':
                return self.data_fetcher.get_leave_data()
            
            elif query_type == 'payroll_query':
                month = parameters.get('month')
                year = parameters.get('year')
                return self.data_fetcher.get_payroll_data(month, year)
            
            elif query_type == 'team_query':
                return self.data_fetcher.get_team_data()
            
            elif query_type == 'company_query':
                return self.data_fetcher.get_company_data()
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching real data: {str(e)}")
            return None
    
    def _generate_enhanced_response(self, query: str, analysis: Dict[str, Any], data: Optional[Dict[str, Any]], user_role: str) -> str:
        """
        Generate response using real data
        """
        try:
            query_type = analysis.get('query_type', 'unknown')
            
            # Try LLM first if available
            if self._is_llm_available():
                try:
                    return self._call_llm_with_data(query, analysis, data, user_role)
                except Exception as e:
                    logger.warning(f"LLM call failed: {str(e)}")
            
            # Fallback to rule-based responses with real data
            return self._generate_rule_based_response(query, analysis, data, user_role)
            
        except Exception as e:
            logger.error(f"Error generating enhanced response: {str(e)}")
            return "Sorry, I encountered an error while generating a response."
    
    def _generate_rule_based_response(self, query: str, analysis: Dict[str, Any], data: Optional[Dict[str, Any]], user_role: str) -> str:
        """
        Generate rule-based response with real data
        """
        query_type = analysis.get('query_type', 'unknown')
        
        if query_type == 'email_query':
            if data and 'email' in data:
                return f"Your email address is: {data['email']}"
            else:
                return "I couldn't find your email address in the system."
        
        elif query_type == 'phone_query':
            if data and 'phone' in data:
                return f"Your phone number is: {data['phone']}"
            else:
                return "I couldn't find your phone number in the system."
        
        elif query_type == 'employee_id_query':
            if data and 'employee_id_number' in data:
                return f"Your employee ID is: {data['employee_id_number']}"
            else:
                return "I couldn't find your employee ID in the system."
        
        elif query_type == 'attendance_query':
            if data and 'error' not in data:
                present_days = data.get('present_days', 0)
                total_days = data.get('total_days', 0)
                percentage = data.get('attendance_percentage', 0)
                period = data.get('period', 'current period')
                
                response = f"Your attendance for {period}:\n"
                response += f"• Present: {present_days} days\n"
                response += f"• Total: {total_days} days\n"
                response += f"• Attendance Rate: {percentage}%"
                
                # Add recent attendance
                recent = data.get('recent_attendance', [])
                if recent:
                    response += "\n\nRecent attendance:"
                    for record in recent[:3]:
                        response += f"\n• {record['date']}: {record['status']}"
                        if record['check_in'] != 'N/A':
                            response += f" (In: {record['check_in']}, Out: {record['check_out']})"
                
                return response
            else:
                return "I couldn't retrieve your attendance data. Please try again later."
        
        elif query_type == 'leave_query':
            if data and 'error' not in data:
                leave_balance = data.get('leave_balance', {})
                recent_requests = data.get('recent_requests', [])
                
                response = "Your leave information:\n\n"
                
                if leave_balance:
                    response += "Leave Balance:\n"
                    for leave_type, balance in leave_balance.items():
                        response += f"• {leave_type}: {balance['remaining']} days remaining (Used: {balance['used']}/{balance['allocated']})\n"
                
                if recent_requests:
                    response += "\nRecent Leave Requests:\n"
                    for request in recent_requests[:3]:
                        response += f"• {request['leave_type']}: {request['start_date']} to {request['end_date']} ({request['status']})\n"
                
                return response
            else:
                return "I couldn't retrieve your leave data. Please try again later."
        
        elif query_type == 'payroll_query':
            if data and 'error' not in data:
                month = data.get('month', 'N/A')
                year = data.get('year', 'N/A')
                net_salary = data.get('net_salary', 0)
                gross_salary = data.get('gross_salary', 0)
                deductions = data.get('total_deductions', 0)
                
                response = f"Your payroll for {month}/{year}:\n"
                response += f"• Gross Salary: ₹{gross_salary:,.2f}\n"
                response += f"• Total Deductions: ₹{deductions:,.2f}\n"
                response += f"• Net Salary: ₹{net_salary:,.2f}"
                
                return response
            else:
                return "I couldn't retrieve your payroll data. Please try again later."
        
        elif query_type == 'profile_query':
            if data and 'error' not in data:
                response = "Your profile information:\n"
                response += f"• Name: {data.get('full_name', 'N/A')}\n"
                response += f"• Employee ID: {data.get('employee_id_number', 'N/A')}\n"
                response += f"• Email: {data.get('email', 'N/A')}\n"
                response += f"• Phone: {data.get('phone', 'N/A')}\n"
                response += f"• Department: {data.get('department', 'N/A')}\n"
                response += f"• Position: {data.get('job_position', 'N/A')}\n"
                response += f"• Manager: {data.get('reporting_manager', 'N/A')}"
                
                return response
            else:
                return "I couldn't retrieve your profile information. Please try again later."
        
        elif query_type == 'team_query':
            if data and 'error' not in data:
                team_size = data.get('team_size', 0)
                team_members = data.get('team_members', [])
                
                response = f"Your team information:\n"
                response += f"• Team Size: {team_size} members\n\n"
                
                if team_members:
                    response += "Team Members:\n"
                    for member in team_members:
                        response += f"• {member['name']} - {member['job_position']} ({member['department']})\n"
                
                return response
            else:
                return "I couldn't retrieve your team information. Please try again later."
        
        elif query_type == 'company_query':
            if data and 'error' not in data:
                total_employees = data.get('total_employees', 0)
                present_today = data.get('present_today', 0)
                attendance_percentage = data.get('attendance_percentage', 0)
                pending_leaves = data.get('pending_leave_requests', 0)
                
                response = "Company Overview:\n"
                response += f"• Total Employees: {total_employees}\n"
                response += f"• Present Today: {present_today}\n"
                response += f"• Today's Attendance: {attendance_percentage}%\n"
                response += f"• Pending Leave Requests: {pending_leaves}"
                
                return response
            else:
                return "I couldn't retrieve company information. Please try again later."
        
        elif query_type == 'greeting_query':
            return f"Hello! I'm Chart Bot, your AI-powered HR Assistant. I can help you with:\n• Your personal information (email, phone, employee ID)\n• Attendance records\n• Leave balance and requests\n• Payroll information\n• Profile details\n\nWhat would you like to know?"
        
        elif query_type == 'help_query':
            return "I can help you with:\n• Personal info: 'What is my email?' or 'My phone number'\n• Attendance: 'My attendance' or 'Show my attendance'\n• Leave: 'My leave balance' or 'Leave requests'\n• Payroll: 'My salary' or 'Payslip'\n• Profile: 'My profile' or 'Employee details'\n\nJust ask me naturally!"
        
        else:
            return f"I'm here to help with HR-related queries! I can assist with your personal information, attendance, leave, payroll, and profile details. You're logged in as {self.user.username} ({user_role}). What would you like to know?"
    
    def _is_llm_available(self) -> bool:
        """
        Check if LLM is available
        """
        try:
            response = requests.get(self.llm_endpoint.replace('/generate', '/tags'), timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _call_llm_with_data(self, query: str, analysis: Dict[str, Any], data: Optional[Dict[str, Any]], user_role: str) -> str:
        """
        Call LLM with real data context
        """
        try:
            # Build context with real data
            context = {
                'query': query,
                'analysis': analysis,
                'data': data,
                'user_role': user_role,
                'user': self.user.username
            }
            
            # Create prompt with real data
            prompt = f"""You are Chart Bot, an AI-powered HR Assistant. Answer the user's query using the provided real data.

User: {self.user.username}
Role: {user_role}
Query: {query}

Real Data Available: {json.dumps(data, indent=2) if data else 'No specific data'}

Please provide a helpful, professional response using the real data. Be concise and conversational.

Response:"""
            
            # Call LLM
            payload = {
                "model": self.llm_model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                self.llm_endpoint,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Sorry, I couldn\'t generate a response.')
            else:
                logger.error(f"LLM API error: {response.status_code}")
                return self._generate_rule_based_response(query, analysis, data, user_role)
                
        except Exception as e:
            logger.error(f"Error calling LLM with data: {str(e)}")
            return self._generate_rule_based_response(query, analysis, data, user_role)
    
    def _create_response(self, success: bool, response: str, status: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create standardized response
        """
        return {
            'success': success,
            'response': response,
            'status': status,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'user_role': self._get_user_role()
        }
