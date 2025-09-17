"""
LangGraph Agent Implementation for Chart Bot
"""
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime, date
import logging
import uuid

try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
except ImportError:
    # Fallback for when LangGraph is not installed
    class StateGraph:
        def __init__(self, state_type):
            pass
        def add_node(self, name, func):
            pass
        def add_edge(self, from_node, to_node):
            pass
        def add_conditional_edges(self, from_node, condition_func, mapping):
            pass
        def set_entry_point(self, node):
            pass
        def compile(self):
            return self
        def invoke(self, state):
            return state
    
    END = "END"
    
    def add_messages(messages):
        return messages
    
    class BaseMessage:
        def __init__(self, content):
            self.content = content
    
    class HumanMessage(BaseMessage):
        pass
    
    class AIMessage(BaseMessage):
        pass
    
    class SystemMessage(BaseMessage):
        pass

from .llm_client import LLMClient
from .security import SecurityManager
from .data_fetcher import DataFetcher
from .query_analyzer import QueryAnalyzer
from ..models import ChatSession, ChatMessage, BotConfiguration

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """
    State for the LangGraph agent
    """
    messages: Annotated[List[BaseMessage], add_messages]
    user_query: str
    user_role: str
    security_context: Dict[str, Any]
    query_analysis: Dict[str, Any]
    data_result: Optional[Dict[str, Any]]
    permission_check: Dict[str, Any]
    final_response: str
    session_id: str
    error: Optional[str]


class ChartBotAgent:
    """
    LangGraph-based Chart Bot Agent
    """
    
    def __init__(self, user, session_id: str = None):
        self.user = user
        self.session_id = session_id or str(uuid.uuid4())
        self.security_manager = SecurityManager(user)
        self.data_fetcher = DataFetcher(self.security_manager)
        self.query_analyzer = QueryAnalyzer()
        
        # Get bot configuration
        try:
            self.config = BotConfiguration.objects.first()
            if not self.config:
                self.config = BotConfiguration.objects.create()
        except:
            self.config = BotConfiguration.objects.create()
        
        self.llm_client = LLMClient(
            endpoint=self.config.llm_endpoint,
            model=self.config.llm_model
        )
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_query", self._analyze_query_node)
        workflow.add_node("check_permissions", self._check_permissions_node)
        workflow.add_node("fetch_data", self._fetch_data_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Add edges
        workflow.set_entry_point("analyze_query")
        
        workflow.add_edge("analyze_query", "check_permissions")
        
        workflow.add_conditional_edges(
            "check_permissions",
            self._should_fetch_data,
            {
                "fetch_data": "fetch_data",
                "generate_response": "generate_response",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("fetch_data", "generate_response")
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _analyze_query_node(self, state: AgentState) -> AgentState:
        """
        Analyze the user query
        """
        try:
            query = state["user_query"]
            analysis = self.query_analyzer.analyze_query(query)
            
            state["query_analysis"] = analysis
            state["security_context"] = self.security_manager.get_security_context()
            
            logger.info(f"Query analyzed: {analysis}")
            
        except Exception as e:
            logger.error(f"Error in analyze_query_node: {str(e)}")
            state["error"] = f"Failed to analyze query: {str(e)}"
        
        return state
    
    def _check_permissions_node(self, state: AgentState) -> AgentState:
        """
        Check user permissions for the query
        """
        try:
            analysis = state["query_analysis"]
            required_permissions = self.query_analyzer.get_required_permissions(analysis)
            
            permission_results = {}
            all_allowed = True
            
            for permission in required_permissions:
                target_employee_id = None
                if analysis.get("target_employee") == "self":
                    target_employee_id = self.security_manager.employee.id if self.security_manager.employee else None
                
                result = self.security_manager.validate_query_permissions(permission, target_employee_id)
                permission_results[permission] = result
                
                if not result["allowed"]:
                    all_allowed = False
            
            state["permission_check"] = {
                "required_permissions": required_permissions,
                "permission_results": permission_results,
                "all_allowed": all_allowed
            }
            
            logger.info(f"Permission check completed: {permission_results}")
            
        except Exception as e:
            logger.error(f"Error in check_permissions_node: {str(e)}")
            state["error"] = f"Failed to check permissions: {str(e)}"
        
        return state
    
    def _should_fetch_data(self, state: AgentState) -> str:
        """
        Determine if data should be fetched or if we should go directly to response
        """
        if state.get("error"):
            return "error"
        
        permission_check = state.get("permission_check", {})
        if not permission_check.get("all_allowed", False):
            return "generate_response"
        
        analysis = state.get("query_analysis", {})
        intent = analysis.get("intent", "general")
        
        # Only fetch data for specific intents
        if intent in ["attendance", "leave", "payroll", "profile", "team", "company"]:
            return "fetch_data"
        
        return "generate_response"
    
    def _fetch_data_node(self, state: AgentState) -> AgentState:
        """
        Fetch data based on query analysis
        """
        try:
            analysis = state["query_analysis"]
            intent = analysis["intent"]
            time_period = analysis["time_period"]
            target_employee = analysis["target_employee"]
            
            # Convert time period to actual dates
            start_date, end_date = self._convert_time_period(time_period)
            
            # Determine target employee ID
            employee_id = None
            if target_employee == "self":
                employee_id = self.security_manager.employee.id if self.security_manager.employee else None
            
            # Fetch data based on intent
            if intent == "attendance":
                data = self.data_fetcher.get_attendance_data(employee_id, start_date, end_date)
            elif intent == "leave":
                data = self.data_fetcher.get_leave_data(employee_id, start_date, end_date)
            elif intent == "payroll":
                month = time_period.get("month")
                year = time_period.get("year")
                data = self.data_fetcher.get_payroll_data(employee_id, month, year)
            elif intent == "profile":
                data = self.data_fetcher.get_employee_profile(employee_id)
            elif intent == "team":
                if intent == "attendance":
                    data = self.data_fetcher.get_attendance_data(None, start_date, end_date)
                elif intent == "leave":
                    data = self.data_fetcher.get_leave_data(None, start_date, end_date)
                else:
                    data = {"error": "Team data not available for this query type"}
            elif intent == "company":
                data = self.data_fetcher.get_company_statistics()
            else:
                data = {"error": "Unknown query type"}
            
            state["data_result"] = data
            
            logger.info(f"Data fetched for intent {intent}: {type(data)}")
            
        except Exception as e:
            logger.error(f"Error in fetch_data_node: {str(e)}")
            state["error"] = f"Failed to fetch data: {str(e)}"
        
        return state
    
    def _generate_response_node(self, state: AgentState) -> AgentState:
        """
        Generate final response using LLM
        """
        try:
            query = state["user_query"]
            analysis = state["query_analysis"]
            permission_check = state["permission_check"]
            data_result = state.get("data_result")
            security_context = state["security_context"]
            
            # Prepare context for LLM
            context = {
                "user_role": security_context["user_role"],
                "query_analysis": analysis,
                "permission_check": permission_check,
                "data_result": data_result,
                "security_context": security_context
            }
            
            # Generate response
            response = self.llm_client.generate_response(query, context)
            state["final_response"] = response
            
            logger.info(f"Response generated: {len(response)} characters")
            
        except Exception as e:
            logger.error(f"Error in generate_response_node: {str(e)}")
            state["error"] = f"Failed to generate response: {str(e)}"
            state["final_response"] = "Sorry, I encountered an error while processing your request. Please try again."
        
        return state
    
    def _handle_error_node(self, state: AgentState) -> AgentState:
        """
        Handle errors and generate error response
        """
        error = state.get("error", "Unknown error occurred")
        permission_check = state.get("permission_check", {})
        
        # Check if it's a permission error
        if not permission_check.get("all_allowed", True):
            permission_results = permission_check.get("permission_results", {})
            for permission, result in permission_results.items():
                if not result["allowed"]:
                    state["final_response"] = result["reason"]
                    if result.get("suggested_action"):
                        state["final_response"] += f" {result['suggested_action']}"
                    break
        else:
            state["final_response"] = f"Sorry, I encountered an error: {error}"
        
        return state
    
    def _convert_time_period(self, time_period: Dict[str, Any]) -> tuple:
        """
        Convert time period to start and end dates
        """
        today = date.today()
        period_type = time_period.get("type", "this_month")
        
        if period_type == "today":
            return today, today
        elif period_type == "yesterday":
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday
        elif period_type == "this_week":
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, end
        elif period_type == "last_week":
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
            return start, end
        elif period_type == "this_month":
            start = today.replace(day=1)
            if today.month == 12:
                end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            return start, end
        elif period_type == "last_month":
            if today.month == 1:
                start = today.replace(year=today.year - 1, month=12, day=1)
            else:
                start = today.replace(month=today.month - 1, day=1)
            end = today.replace(day=1) - timedelta(days=1)
            return start, end
        elif period_type == "this_year":
            start = today.replace(month=1, day=1)
            end = today.replace(month=12, day=31)
            return start, end
        elif period_type == "last_year":
            start = today.replace(year=today.year - 1, month=1, day=1)
            end = today.replace(year=today.year - 1, month=12, day=31)
            return start, end
        elif period_type == "specific_date":
            specific_date = time_period.get("start_date")
            if specific_date:
                return specific_date, specific_date
        else:
            # Default to this month
            start = today.replace(day=1)
            if today.month == 12:
                end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            return start, end
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query through the LangGraph workflow
        """
        try:
            # Get or create chat session
            session, created = ChatSession.objects.get_or_create(
                session_id=self.session_id,
                user=self.user,
                defaults={'is_active': True}
            )
            
            # Create initial state
            initial_state = AgentState(
                messages=[HumanMessage(content=query)],
                user_query=query,
                user_role=self.security_manager.user_role,
                security_context=self.security_manager.get_security_context(),
                query_analysis={},
                data_result=None,
                permission_check={},
                final_response="",
                session_id=self.session_id,
                error=None
            )
            
            # Run the graph
            result = self.graph.invoke(initial_state)
            
            # Save the conversation
            self._save_conversation(session, query, result["final_response"])
            
            return {
                "response": result["final_response"],
                "session_id": self.session_id,
                "user_role": result["user_role"],
                "query_analysis": result.get("query_analysis", {}),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "response": "Sorry, I encountered an error while processing your request. Please try again.",
                "session_id": self.session_id,
                "error": str(e),
                "success": False
            }
    
    def _save_conversation(self, session: ChatSession, user_query: str, bot_response: str):
        """
        Save the conversation to database
        """
        try:
            # Save user message
            ChatMessage.objects.create(
                session=session,
                message_type='user',
                content=user_query
            )
            
            # Save bot response
            ChatMessage.objects.create(
                session=session,
                message_type='bot',
                content=bot_response
            )
            
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history for the session
        """
        try:
            session = ChatSession.objects.get(session_id=self.session_id)
            messages = ChatMessage.objects.filter(session=session).order_by('-timestamp')[:limit]
            
            history = []
            for message in reversed(messages):
                history.append({
                    "type": message.message_type,
                    "content": message.content,
                    "timestamp": message.timestamp
                })
            
            return history
            
        except ChatSession.DoesNotExist:
            return []
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
