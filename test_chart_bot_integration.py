#!/usr/bin/env python
"""
Chart Bot Integration Test Script
Tests the complete Chart Bot functionality
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.contrib.auth.models import User
from chart_bot.models import BotConfiguration, ChatSession, ChatMessage
from chart_bot.core.security import SecurityManager
from chart_bot.core.query_analyzer import QueryAnalyzer
from chart_bot.core.data_fetcher import DataFetcher
from chart_bot.core.llm_client import LLMClient


def test_models():
    """Test model creation and relationships"""
    print("🧪 Testing Models...")
    
    try:
        # Test BotConfiguration
        config = BotConfiguration.objects.create(
            name="Test Bot",
            is_enabled=True,
            llm_endpoint="http://125.18.84.108:11434/api/generate",
            llm_model="mistral"
        )
        print("✅ BotConfiguration created successfully")
        
        # Test ChatSession
        user = User.objects.first()
        if not user:
            print("⚠️ No users found, creating test user...")
            user = User.objects.create_user(
                username="testuser",
                email="test@example.com",
                password="testpass123"
            )
        
        session = ChatSession.objects.create(
            user=user,
            session_id="test-session-123",
            is_active=True
        )
        print("✅ ChatSession created successfully")
        
        # Test ChatMessage
        message = ChatMessage.objects.create(
            session=session,
            message_type="user",
            content="Test message"
        )
        print("✅ ChatMessage created successfully")
        
        # Cleanup
        message.delete()
        session.delete()
        config.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {str(e)}")
        return False


def test_security_manager():
    """Test SecurityManager functionality"""
    print("🔐 Testing Security Manager...")
    
    try:
        user = User.objects.first()
        if not user:
            print("❌ No users found for security test")
            return False
        
        security_manager = SecurityManager(user)
        context = security_manager.get_security_context()
        
        print(f"✅ User role: {context['user_role']}")
        print(f"✅ Accessible employees: {len(context['accessible_employees'])}")
        
        # Test permission validation
        validation = security_manager.validate_query_permissions("attendance")
        print(f"✅ Permission validation: {validation['allowed']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Security manager test failed: {str(e)}")
        return False


def test_query_analyzer():
    """Test QueryAnalyzer functionality"""
    print("🔍 Testing Query Analyzer...")
    
    try:
        analyzer = QueryAnalyzer()
        
        test_queries = [
            "What is my attendance for this month?",
            "Show me my leave balance",
            "What is my salary for August?",
            "Show attendance of my team this month"
        ]
        
        for query in test_queries:
            analysis = analyzer.analyze_query(query)
            print(f"✅ Query: '{query}' -> Intent: {analysis['intent']}, Confidence: {analysis['confidence']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query analyzer test failed: {str(e)}")
        return False


def test_llm_client():
    """Test LLM client connectivity"""
    print("🤖 Testing LLM Client...")
    
    try:
        client = LLMClient()
        
        # Test with a simple prompt
        response = client.generate_response("Hello, are you working?")
        
        if response and len(response) > 0:
            print(f"✅ LLM response received: {response[:100]}...")
            return True
        else:
            print("⚠️ LLM response was empty")
            return False
            
    except Exception as e:
        print(f"❌ LLM client test failed: {str(e)}")
        return False


def test_data_fetcher():
    """Test DataFetcher functionality"""
    print("📊 Testing Data Fetcher...")
    
    try:
        user = User.objects.first()
        if not user:
            print("❌ No users found for data fetcher test")
            return False
        
        security_manager = SecurityManager(user)
        data_fetcher = DataFetcher(security_manager)
        
        # Test employee profile fetching
        if security_manager.employee:
            profile = data_fetcher.get_employee_profile()
            if not profile.get('error'):
                print(f"✅ Employee profile fetched: {profile.get('name', 'Unknown')}")
            else:
                print(f"⚠️ Employee profile error: {profile.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data fetcher test failed: {str(e)}")
        return False


def test_complete_workflow():
    """Test the complete Chart Bot workflow"""
    print("🔄 Testing Complete Workflow...")
    
    try:
        from chart_bot.core.langgraph_agent import ChartBotAgent
        
        user = User.objects.first()
        if not user:
            print("❌ No users found for workflow test")
            return False
        
        agent = ChartBotAgent(user)
        result = agent.process_query("Hello, are you working?")
        
        if result['success']:
            print(f"✅ Complete workflow test successful!")
            print(f"📝 Response: {result['response'][:100]}...")
            return True
        else:
            print(f"⚠️ Workflow test completed with issues: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Complete workflow test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("🚀 Chart Bot Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Models", test_models),
        ("Security Manager", test_security_manager),
        ("Query Analyzer", test_query_analyzer),
        ("LLM Client", test_llm_client),
        ("Data Fetcher", test_data_fetcher),
        ("Complete Workflow", test_complete_workflow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Chart Bot is ready to use.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
