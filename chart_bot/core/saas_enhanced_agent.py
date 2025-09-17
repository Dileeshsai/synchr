"""
SaaS-Enhanced Chart Bot Agent - Multi-tenant, Production-Ready
"""
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
import requests
from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from .enhanced_data_fetcher import EnhancedDataFetcher
from .enhanced_query_analyzer import EnhancedQueryAnalyzer

logger = logging.getLogger(__name__)


class SaaSEnhancedChartBotAgent:
    """
    SaaS-Enhanced Chart Bot Agent with multi-tenancy, caching, and production features
    """
    
    def __init__(self, user, session_id: str = None, company_id: str = None):
        self.user = user
        self.session_id = session_id or f"session_{user.id}_{datetime.now().timestamp()}"
        self.company_id = company_id or self._get_company_id()
        self.data_fetcher = EnhancedDataFetcher(user)
        self.query_analyzer = EnhancedQueryAnalyzer()
        self.llm_endpoint = "http://125.18.84.108:11434/api/generate"
        self.llm_model = "mistral"
        
        # Enhanced memory with caching
        self.conversation_history = self._load_conversation_history()
        self.max_history = 20
        
        # Performance tracking
        self.start_time = datetime.now()
        self.query_count = 0
        
        logger.info(f"SaaS Enhanced Chart Bot Agent initialized for user: {user.username}, company: {self.company_id}")
    
    def _get_company_id(self) -> Optional[str]:
        """
        Get company ID for multi-tenancy
        """
        try:
            if hasattr(self.user, 'employee_get') and self.user.employee_get:
                employee = self.user.employee_get
                work_info = getattr(employee, 'employee_work_info', None)
                if work_info and work_info.company_id:
                    return str(work_info.company_id.id)
            return None
        except Exception as e:
            logger.warning(f"Could not get company ID: {str(e)}")
            return None
    
    def _load_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Load conversation history from cache
        """
        try:
            cache_key = f"chart_bot_history_{self.user.id}_{self.company_id}"
            history = cache.get(cache_key, [])
            return history[-self.max_history:] if history else []
        except Exception as e:
            logger.warning(f"Could not load conversation history: {str(e)}")
            return []
    
    def _save_conversation_history(self):
        """
        Save conversation history to cache
        """
        try:
            cache_key = f"chart_bot_history_{self.user.id}_{self.company_id}"
            cache.set(cache_key, self.conversation_history, timeout=3600)  # 1 hour
        except Exception as e:
            logger.warning(f"Could not save conversation history: {str(e)}")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query with SaaS enhancements
        """
        try:
            self.query_count += 1
            logger.info(f"Processing SaaS query #{self.query_count}: {query}")
            
            # Add to conversation history
            self.conversation_history.append({
                'type': 'user',
                'content': query,
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id
            })
            
            # Analyze query with enhanced context
            analysis = self._enhanced_query_analysis(query)
            logger.info(f"Enhanced query analysis: {analysis}")
            
            # Get user role and permissions
            user_context = self._get_user_context()
            
            # Check SaaS permissions
            if not self._check_saas_permissions(analysis, user_context):
                response = "Sorry, you don't have permission to view this data."
                return self._create_response(False, response, "permission_denied", user_context)
            
            # Fetch data with caching
            data = None
            if analysis.get('requires_data', False):
                data = self._fetch_cached_data(analysis)
                logger.info(f"Cached data fetched: {bool(data)}")
            
            # Generate enhanced response
            response = self._generate_saas_response(query, analysis, data, user_context)
            
            # Add to conversation history
            self.conversation_history.append({
                'type': 'assistant',
                'content': response,
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id,
                'query_type': analysis.get('query_type'),
                'data_used': bool(data)
            })
            
            # Save conversation history
            self._save_conversation_history()
            
            # Performance metrics
            processing_time = (datetime.now() - self.start_time).total_seconds()
            
            return self._create_response(True, response, "success", data, user_context, processing_time)
            
        except Exception as e:
            logger.error(f"Error processing SaaS query: {str(e)}")
            return self._create_response(False, "Sorry, I encountered an error while processing your request.", "error")
    
    def _enhanced_query_analysis(self, query: str) -> Dict[str, Any]:
        """
        Enhanced query analysis with SaaS context
        """
        analysis = self.query_analyzer.analyze_query(query)
        
        # Add SaaS-specific enhancements
        analysis.update({
            'company_id': self.company_id,
            'user_id': self.user.id,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'query_count': self.query_count
        })
        
        return analysis
    
    def _get_user_context(self) -> Dict[str, Any]:
        """
        Get comprehensive user context for SaaS
        """
        try:
            user_role = self._get_user_role()
            employee = getattr(self.user, 'employee_get', None)
            
            context = {
                'user_id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'role': user_role,
                'company_id': self.company_id,
                'is_active': self.user.is_active,
                'is_staff': self.user.is_staff,
                'is_superuser': self.user.is_superuser,
                'employee_id': employee.id if employee else None,
                'employee_name': employee.get_full_name() if employee else None,
                'permissions': self._get_user_permissions(),
                'subscription_tier': self._get_subscription_tier(),
                'features_enabled': self._get_enabled_features()
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting user context: {str(e)}")
            return {
                'user_id': self.user.id,
                'username': self.user.username,
                'role': 'employee',
                'company_id': self.company_id
            }
    
    def _get_user_role(self) -> str:
        """
        Get user role with SaaS enhancements
        """
        if self.user.is_superuser:
            return "admin"
        elif self.user.is_staff:
            return "hr_manager"
        else:
            return "employee"
    
    def _get_user_permissions(self) -> List[str]:
        """
        Get user permissions
        """
        try:
            permissions = []
            if self.user.is_superuser:
                permissions.extend(['view_all', 'manage_all', 'export_data', 'admin_panel'])
            elif self.user.is_staff:
                permissions.extend(['view_team', 'manage_team', 'export_team'])
            else:
                permissions.extend(['view_own'])
            
            # Add specific permissions
            user_permissions = self.user.get_all_permissions()
            permissions.extend(list(user_permissions))
            
            return permissions
        except Exception as e:
            logger.warning(f"Could not get user permissions: {str(e)}")
            return ['view_own']
    
    def _get_subscription_tier(self) -> str:
        """
        Get subscription tier (for SaaS)
        """
        # This would integrate with your subscription system
        try:
            if self.user.is_superuser:
                return "enterprise"
            elif self.user.is_staff:
                return "professional"
            else:
                return "basic"
        except:
            return "basic"
    
    def _get_enabled_features(self) -> List[str]:
        """
        Get enabled features based on subscription
        """
        subscription_tier = self._get_subscription_tier()
        
        features = {
            'basic': ['personal_info', 'attendance', 'leave_balance'],
            'professional': ['personal_info', 'attendance', 'leave_balance', 'team_data', 'reports'],
            'enterprise': ['personal_info', 'attendance', 'leave_balance', 'team_data', 'reports', 'analytics', 'export', 'api_access']
        }
        
        return features.get(subscription_tier, features['basic'])
    
    def _check_saas_permissions(self, analysis: Dict[str, Any], user_context: Dict[str, Any]) -> bool:
        """
        Check SaaS permissions with subscription tiers
        """
        query_type = analysis.get('query_type', 'unknown')
        user_scope = analysis.get('user_scope', 'personal')
        user_role = user_context.get('role', 'employee')
        features_enabled = user_context.get('features_enabled', [])
        
        # Check feature access
        if query_type == 'team_query' and 'team_data' not in features_enabled:
            return False
        if query_type == 'company_query' and 'reports' not in features_enabled:
            return False
        if query_type == 'analytics_query' and 'analytics' not in features_enabled:
            return False
        
        # Check role-based permissions
        if user_role == "admin":
            return True
        elif user_role == "hr_manager":
            return user_scope in ['personal', 'team']
        elif user_role == "employee":
            return user_scope == 'personal'
        
        return False
    
    def _fetch_cached_data(self, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch data with intelligent caching
        """
        try:
            query_type = analysis.get('query_type', 'unknown')
            cache_key = f"chart_bot_data_{self.user.id}_{self.company_id}_{query_type}"
            
            # Try cache first
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Using cached data for {query_type}")
                return cached_data
            
            # Fetch fresh data
            data = self._fetch_real_data(analysis)
            
            # Cache the data
            if data and 'error' not in data:
                cache_timeout = self._get_cache_timeout(query_type)
                cache.set(cache_key, data, timeout=cache_timeout)
                logger.info(f"Cached fresh data for {query_type}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching cached data: {str(e)}")
            return None
    
    def _get_cache_timeout(self, query_type: str) -> int:
        """
        Get cache timeout based on query type
        """
        timeouts = {
            'profile_query': 3600,  # 1 hour
            'attendance_query': 300,  # 5 minutes
            'leave_query': 600,  # 10 minutes
            'payroll_query': 1800,  # 30 minutes
            'team_query': 600,  # 10 minutes
            'company_query': 300,  # 5 minutes
        }
        return timeouts.get(query_type, 300)  # Default 5 minutes
    
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
    
    def _generate_saas_response(self, query: str, analysis: Dict[str, Any], data: Optional[Dict[str, Any]], user_context: Dict[str, Any]) -> str:
        """
        Generate SaaS-enhanced response
        """
        try:
            query_type = analysis.get('query_type', 'unknown')
            user_role = user_context.get('role', 'employee')
            subscription_tier = user_context.get('subscription_tier', 'basic')
            
            # Try LLM first if available
            if self._is_llm_available():
                try:
                    return self._call_llm_with_saas_context(query, analysis, data, user_context)
                except Exception as e:
                    logger.warning(f"LLM call failed: {str(e)}")
            
            # Fallback to rule-based responses
            response = self._generate_rule_based_response(query, analysis, data, user_context)
            
            # Add SaaS enhancements
            if subscription_tier == 'basic' and query_type in ['team_query', 'company_query']:
                response += "\n\n💡 Upgrade to Professional or Enterprise for advanced features!"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating SaaS response: {str(e)}")
            return "Sorry, I encountered an error while generating a response."
    
    def _generate_rule_based_response(self, query: str, analysis: Dict[str, Any], data: Optional[Dict[str, Any]], user_context: Dict[str, Any]) -> str:
        """
        Generate rule-based response with SaaS context
        """
        query_type = analysis.get('query_type', 'unknown')
        user_role = user_context.get('role', 'employee')
        subscription_tier = user_context.get('subscription_tier', 'basic')
        
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
    
    def _call_llm_with_saas_context(self, query: str, analysis: Dict[str, Any], data: Optional[Dict[str, Any]], user_context: Dict[str, Any]) -> str:
        """
        Call LLM with SaaS context
        """
        try:
            # Build comprehensive context
            context = {
                'query': query,
                'analysis': analysis,
                'data': data,
                'user_context': user_context,
                'conversation_history': self.conversation_history[-5:],  # Last 5 messages
                'timestamp': datetime.now().isoformat()
            }
            
            # Create enhanced prompt
            prompt = f"""You are Chart Bot, an AI-powered HR Assistant for a SaaS HRMS platform. Provide helpful, professional responses using the provided real data.

User Context:
- Username: {user_context.get('username', 'N/A')}
- Role: {user_context.get('role', 'employee')}
- Subscription: {user_context.get('subscription_tier', 'basic')}
- Company ID: {user_context.get('company_id', 'N/A')}

Query: {query}

Real Data Available: {json.dumps(data, indent=2) if data else 'No specific data'}

Recent Conversation:
{json.dumps(self.conversation_history[-3:], indent=2) if self.conversation_history else 'No previous conversation'}

Please provide a helpful, professional response using the real data. Be concise, conversational, and SaaS-focused.

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
                return self._generate_rule_based_response(query, analysis, data, user_context)
                
        except Exception as e:
            logger.error(f"Error calling LLM with SaaS context: {str(e)}")
            return self._generate_rule_based_response(query, analysis, data, user_context)
    
    def _create_response(self, success: bool, response: str, status: str, data: Optional[Dict[str, Any]] = None, user_context: Optional[Dict[str, Any]] = None, processing_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Create standardized SaaS response
        """
        return {
            'success': success,
            'response': response,
            'status': status,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'user_context': user_context or {},
            'processing_time': processing_time,
            'query_count': self.query_count,
            'company_id': self.company_id,
            'subscription_tier': user_context.get('subscription_tier', 'basic') if user_context else 'basic'
        }
