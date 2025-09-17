"""
Simple Chart Bot Agent - Fallback implementation without LangGraph
"""
import json
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
import requests

from .security import SecurityManager
from .data_fetcher import DataFetcher
from .query_analyzer import QueryAnalyzer

logger = logging.getLogger(__name__)


class SimpleChartBotAgent:
    """
    Simple Chart Bot Agent that works without LangGraph
    """
    
    def __init__(self, user, session_id: str = None):
        self.user = user
        self.session_id = session_id or f"session_{user.id}_{datetime.now().timestamp()}"
        self.security_manager = SecurityManager(user)
        self.data_fetcher = DataFetcher(user)
        self.query_analyzer = QueryAnalyzer()
        self.llm_endpoint = "http://125.18.84.108:11434/api/generate"
        self.llm_model = "mistral"
        
        # Simple memory storage
        self.conversation_history = []
        self.max_history = 10
        
        logger.info(f"Simple Chart Bot Agent initialized for user: {user.username}")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query using simple logic
        """
        try:
            logger.info(f"Processing query: {query}")
            
            # Add to conversation history
            self.conversation_history.append({
                'type': 'user',
                'content': query,
                'timestamp': datetime.now().isoformat()
            })
            
            # Step 1: Analyze query
            analysis = self.query_analyzer.analyze_query(query)
            logger.info(f"Query analysis: {analysis}")
            
            # Step 2: Check security permissions
            security_context = self.security_manager.get_security_context()
            if not self._check_permissions(analysis, security_context):
                response = "Sorry, you don't have permission to view this data."
                return self._create_response(False, response, "permission_denied")
            
            # Step 3: Fetch data if needed
            data = None
            if analysis.get('requires_data', False):
                data = self._fetch_data(analysis)
                logger.info(f"Data fetched: {data}")
            
            # Step 4: Generate response using LLM
            response = self._generate_response(query, analysis, data, security_context)
            
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
            logger.error(f"Error processing query: {str(e)}")
            return self._create_response(False, "Sorry, I encountered an error while processing your request.", "error")
    
    def _check_permissions(self, analysis: Dict[str, Any], security_context: Dict[str, Any]) -> bool:
        """
        Check if user has permissions for the query
        """
        try:
            query_type = analysis.get('query_type', 'unknown')
            user_role = security_context.get('user_role', 'unknown')
            
            # Simple permission logic
            if query_type == 'personal_data':
                return True  # Users can always access their own data
            
            elif query_type == 'team_data':
                return user_role in ['hr_manager', 'admin']
            
            elif query_type == 'company_data':
                return user_role == 'admin'
            
            elif query_type == 'other_employee_data':
                return user_role in ['hr_manager', 'admin']
            
            else:
                return True  # Allow general queries
            
        except Exception as e:
            logger.error(f"Error checking permissions: {str(e)}")
            return False
    
    def _fetch_data(self, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch data based on analysis
        """
        try:
            query_type = analysis.get('query_type', 'unknown')
            
            if query_type == 'personal_data':
                return self.data_fetcher.get_personal_data(analysis)
            elif query_type == 'team_data':
                return self.data_fetcher.get_team_data(analysis)
            elif query_type == 'company_data':
                return self.data_fetcher.get_company_data(analysis)
            elif query_type == 'attendance_data':
                return self.data_fetcher.get_attendance_data(analysis)
            elif query_type == 'leave_data':
                return self.data_fetcher.get_leave_data(analysis)
            elif query_type == 'payroll_data':
                return self.data_fetcher.get_payroll_data(analysis)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return None
    
    def _generate_response(self, query: str, analysis: Dict[str, Any], data: Optional[Dict[str, Any]], security_context: Dict[str, Any]) -> str:
        """
        Generate response using LLM or fallback logic
        """
        try:
            # Try to use LLM first
            if self._is_llm_available():
                return self._call_llm(query, analysis, data, security_context)
            else:
                # Fallback to simple response generation
                return self._generate_simple_response(query, analysis, data, security_context)
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._generate_simple_response(query, analysis, data, security_context)
    
    def _is_llm_available(self) -> bool:
        """
        Check if LLM is available
        """
        try:
            response = requests.get(self.llm_endpoint.replace('/generate', '/tags'), timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _call_llm(self, query: str, analysis: Dict[str, Any], data: Optional[Dict[str, Any]], security_context: Dict[str, Any]) -> str:
        """
        Call the LLM to generate response
        """
        try:
            # Build context
            context = {
                'query': query,
                'analysis': analysis,
                'data': data,
                'security_context': security_context,
                'conversation_history': self.conversation_history[-5:]  # Last 5 messages
            }
            
            # Create prompt
            prompt = self._build_prompt(context)
            
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
                return self._generate_simple_response(query, analysis, data, security_context)
                
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            return self._generate_simple_response(query, analysis, data, security_context)
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build prompt for LLM
        """
        prompt = f"""You are Chart Bot, an AI-powered HR Assistant. You help employees, HR managers, and admins with HR-related queries.

User Role: {context['security_context'].get('user_role', 'unknown')}
Query: {context['query']}
Query Type: {context['analysis'].get('query_type', 'unknown')}

Data Available: {json.dumps(context['data'], indent=2) if context['data'] else 'No specific data'}

Please provide a helpful, professional response. Keep it concise and relevant. If the user doesn't have permission for certain data, politely explain that.

Response:"""
        
        return prompt
    
    def _generate_simple_response(self, query: str, analysis: Dict[str, Any], data: Optional[Dict[str, Any]], security_context: Dict[str, Any]) -> str:
        """
        Generate simple response without LLM
        """
        query_type = analysis.get('query_type', 'unknown')
        user_role = security_context.get('user_role', 'unknown')
        
        # Simple response templates
        if query_type == 'personal_data':
            if data:
                return f"Here's your personal information: {json.dumps(data, indent=2)}"
            else:
                return "I can help you with your personal HR information. What specific details would you like to know?"
        
        elif query_type == 'team_data':
            if user_role in ['hr_manager', 'admin']:
                if data:
                    return f"Here's your team information: {json.dumps(data, indent=2)}"
                else:
                    return "I can help you with your team's information. What would you like to know?"
            else:
                return "Sorry, you don't have permission to view team data."
        
        elif query_type == 'company_data':
            if user_role == 'admin':
                if data:
                    return f"Here's the company information: {json.dumps(data, indent=2)}"
                else:
                    return "I can help you with company-wide information. What would you like to know?"
            else:
                return "Sorry, you don't have permission to view company-wide data."
        
        elif query_type == 'attendance_data':
            if data:
                return f"Here's the attendance information: {json.dumps(data, indent=2)}"
            else:
                return "I can help you with attendance information. What would you like to know?"
        
        elif query_type == 'leave_data':
            if data:
                return f"Here's the leave information: {json.dumps(data, indent=2)}"
            else:
                return "I can help you with leave information. What would you like to know?"
        
        elif query_type == 'payroll_data':
            if data:
                return f"Here's the payroll information: {json.dumps(data, indent=2)}"
            else:
                return "I can help you with payroll information. What would you like to know?"
        
        else:
            return "Hello! I'm Chart Bot, your AI-powered HR Assistant. I can help you with attendance, leave, payroll, and other HR-related queries. What would you like to know?"
    
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
            'user_role': self.security_manager.get_security_context().get('user_role', 'unknown')
        }
