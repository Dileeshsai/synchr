"""
LLM Client for Chart Bot
Handles communication with the custom LLM endpoint
"""
import json
import requests
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for communicating with the custom LLM endpoint
    """
    
    def __init__(self, endpoint: str = "http://125.18.84.108:11434/api/generate", model: str = "mistral"):
        self.endpoint = endpoint
        self.model = model
        self.timeout = 30
    
    def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a response from the LLM
        
        Args:
            prompt: The input prompt
            context: Additional context for the prompt
            
        Returns:
            Generated response text
        """
        try:
            # Prepare the full prompt with context
            full_prompt = self._prepare_prompt(prompt, context)
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False
            }
            
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Sorry, I could not generate a response.')
            else:
                logger.error(f"LLM API error: {response.status_code} - {response.text}")
                return "Sorry, I'm having trouble connecting to the AI service right now."
                
        except requests.exceptions.Timeout:
            logger.error("LLM request timeout")
            return "Sorry, the request is taking too long. Please try again."
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM request error: {str(e)}")
            return "Sorry, I'm having trouble connecting to the AI service right now."
        except Exception as e:
            logger.error(f"Unexpected error in LLM client: {str(e)}")
            return "Sorry, an unexpected error occurred. Please try again."
    
    def _prepare_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Prepare the full prompt with context and instructions
        """
        system_instructions = """You are Chart Bot, an AI-powered HR Assistant integrated with the company's HRMS. 
Your role is to help employees, HR managers, and admins with HR-related queries while strictly following role-based access rules.

IMPORTANT SECURITY RULES:
1. Always respect user roles (Employee/HR Manager/Admin)
2. Never reveal unauthorized data
3. If access is denied, politely refuse with security-compliant messages
4. Keep responses professional, concise, and conversational
5. Use bullet points or tables for structured data
6. Never reveal raw SQL queries, schemas, or backend logic

RESPONSE FORMAT:
- Be friendly and professional
- Keep answers short and to the point
- Use bullet points for lists
- Offer helpful follow-ups when appropriate
- Always maintain data security and privacy

"""
        
        if context:
            context_str = f"\nCONTEXT:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            context_str += "\n"
        else:
            context_str = ""
        
        return f"{system_instructions}{context_str}USER QUERY: {prompt}\n\nRESPONSE:"
