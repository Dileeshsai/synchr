"""
Ultra Simple Chart Bot Agent - No complex dependencies
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class UltraSimpleChartBotAgent:
    """
    Ultra Simple Chart Bot Agent with minimal dependencies
    """
    
    def __init__(self, user, session_id: str = None):
        self.user = user
        self.session_id = session_id or f"session_{user.id}_{datetime.now().timestamp()}"
        self.llm_endpoint = "http://125.18.84.108:11434/api/generate"
        self.llm_model = "mistral"
        
        # Simple memory storage
        self.conversation_history = []
        self.max_history = 10
        
        logger.info(f"Ultra Simple Chart Bot Agent initialized for user: {user.username}")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query using ultra simple logic
        """
        try:
            logger.info(f"Processing query: {query}")
            
            # Add to conversation history
            self.conversation_history.append({
                'type': 'user',
                'content': query,
                'timestamp': datetime.now().isoformat()
            })
            
            # Simple query analysis
            query_lower = query.lower()
            
            # Determine user role
            user_role = self._get_user_role()
            
            # Check permissions
            if not self._check_simple_permissions(query_lower, user_role):
                response = "Sorry, you don't have permission to view this data."
                return self._create_response(False, response, "permission_denied")
            
            # Generate response
            response = self._generate_simple_response(query, query_lower, user_role)
            
            # Add to conversation history
            self.conversation_history.append({
                'type': 'assistant',
                'content': response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Trim history
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            return self._create_response(True, response, "success")
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return self._create_response(False, "Sorry, I encountered an error while processing your request.", "error")
    
    def _get_user_role(self) -> str:
        """
        Get simple user role
        """
        if self.user.is_superuser:
            return "admin"
        elif self.user.is_staff:
            return "hr_manager"
        else:
            return "employee"
    
    def _check_simple_permissions(self, query_lower: str, user_role: str) -> bool:
        """
        Simple permission check
        """
        # Admin can access everything
        if user_role == "admin":
            return True
        
        # HR manager can access most things
        if user_role == "hr_manager":
            return True
        
        # Employee can only access personal data
        if user_role == "employee":
            personal_keywords = [
                "my", "personal", "own", "myself", "i", "me",
                "attendance", "leave", "payroll", "profile"
            ]
            return any(keyword in query_lower for keyword in personal_keywords)
        
        return False
    
    def _generate_simple_response(self, query: str, query_lower: str, user_role: str) -> str:
        """
        Generate simple response
        """
        # Try LLM first
        try:
            if self._is_llm_available():
                return self._call_llm(query, user_role)
        except Exception as e:
            logger.warning(f"LLM call failed: {str(e)}")
        
        # Fallback to simple responses
        if "hello" in query_lower or "hi" in query_lower:
            return f"Hello! I'm Chart Bot, your AI-powered HR Assistant. I can help you with HR-related queries. You are logged in as {self.user.username} with {user_role} role."
        
        elif "attendance" in query_lower:
            return "I can help you with attendance information. What specific attendance details would you like to know?"
        
        elif "leave" in query_lower:
            return "I can help you with leave information. What leave details would you like to know?"
        
        elif "payroll" in query_lower or "salary" in query_lower:
            return "I can help you with payroll information. What payroll details would you like to know?"
        
        elif "profile" in query_lower or "personal" in query_lower:
            return "I can help you with your personal profile information. What would you like to know?"
        
        elif "team" in query_lower and user_role in ["hr_manager", "admin"]:
            return "I can help you with team information. What team details would you like to know?"
        
        elif "company" in query_lower and user_role == "admin":
            return "I can help you with company-wide information. What company details would you like to know?"
        
        else:
            return f"I'm here to help with HR-related queries! I can assist with attendance, leave, payroll, and profile information. You're currently logged in as {self.user.username} ({user_role}). What would you like to know?"
    
    def _is_llm_available(self) -> bool:
        """
        Check if LLM is available
        """
        try:
            response = requests.get(self.llm_endpoint.replace('/generate', '/tags'), timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _call_llm(self, query: str, user_role: str) -> str:
        """
        Call the LLM to generate response
        """
        try:
            # Build simple prompt
            prompt = f"""You are Chart Bot, an AI-powered HR Assistant. 

User Role: {user_role}
User: {self.user.username}
Query: {query}

Please provide a helpful, professional response about HR topics. Keep it concise and relevant.

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
                return self._generate_fallback_response(query, user_role)
                
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            return self._generate_fallback_response(query, user_role)
    
    def _generate_fallback_response(self, query: str, user_role: str) -> str:
        """
        Generate fallback response when LLM is not available
        """
        return f"I'm Chart Bot, your HR Assistant. I can help you with HR queries. You're logged in as {self.user.username} ({user_role}). What would you like to know about attendance, leave, payroll, or your profile?"
    
    def _create_response(self, success: bool, response: str, status: str) -> Dict[str, Any]:
        """
        Create standardized response
        """
        return {
            'success': success,
            'response': response,
            'status': status,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'user_role': self._get_user_role()
        }
