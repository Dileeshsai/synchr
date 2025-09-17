#!/usr/bin/env python
"""
SaaS Chart Bot Verification Script
Comprehensive testing and verification of the enhanced Chart Bot
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.contrib.auth.models import User
from chart_bot.core.saas_enhanced_agent import SaaSEnhancedChartBotAgent
from chart_bot.core.enhanced_data_fetcher import EnhancedDataFetcher
from chart_bot.core.enhanced_query_analyzer import EnhancedQueryAnalyzer


def test_imports():
    """Test all imports are working"""
    print("🔍 Testing imports...")
    try:
        from chart_bot.core.saas_enhanced_agent import SaaSEnhancedChartBotAgent
        from chart_bot.core.enhanced_data_fetcher import EnhancedDataFetcher
        from chart_bot.core.enhanced_query_analyzer import EnhancedQueryAnalyzer
        print("✅ All imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False


def test_user_authentication():
    """Test user authentication and employee data"""
    print("\n🔍 Testing user authentication...")
    try:
        # Get a test user
        user = User.objects.filter(is_active=True).first()
        if not user:
            print("❌ No active users found")
            return False
        
        print(f"✅ Found user: {user.username}")
        
        # Test employee data
        if hasattr(user, 'employee_get') and user.employee_get:
            employee = user.employee_get
            print(f"✅ Employee found: {employee.get_full_name()}")
            print(f"   - Email: {employee.email}")
            print(f"   - Phone: {employee.phone}")
            print(f"   - Badge ID: {employee.badge_id}")
            return True
        else:
            print("⚠️ No employee record found for user")
            return False
            
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return False


def test_data_fetcher():
    """Test the enhanced data fetcher"""
    print("\n🔍 Testing enhanced data fetcher...")
    try:
        user = User.objects.filter(is_active=True).first()
        if not user:
            print("❌ No user found for testing")
            return False
        
        fetcher = EnhancedDataFetcher(user)
        
        # Test personal info
        personal_info = fetcher.get_personal_info()
        print(f"✅ Personal info fetched: {bool(personal_info)}")
        if personal_info and 'error' not in personal_info:
            print(f"   - Name: {personal_info.get('full_name', 'N/A')}")
            print(f"   - Email: {personal_info.get('email', 'N/A')}")
        
        # Test attendance data
        attendance_data = fetcher.get_attendance_data()
        print(f"✅ Attendance data fetched: {bool(attendance_data)}")
        if attendance_data and 'error' not in attendance_data:
            print(f"   - Present days: {attendance_data.get('present_days', 0)}")
            print(f"   - Attendance rate: {attendance_data.get('attendance_percentage', 0)}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Data fetcher error: {str(e)}")
        return False


def test_query_analyzer():
    """Test the enhanced query analyzer"""
    print("\n🔍 Testing enhanced query analyzer...")
    try:
        analyzer = EnhancedQueryAnalyzer()
        
        test_queries = [
            "What is my email address?",
            "Show my attendance",
            "My leave balance",
            "What is my salary?",
            "My profile information"
        ]
        
        for query in test_queries:
            analysis = analyzer.analyze_query(query)
            print(f"✅ Query: '{query}' -> Type: {analysis.get('query_type', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query analyzer error: {str(e)}")
        return False


def test_saas_agent():
    """Test the SaaS enhanced agent"""
    print("\n🔍 Testing SaaS enhanced agent...")
    try:
        user = User.objects.filter(is_active=True).first()
        if not user:
            print("❌ No user found for testing")
            return False
        
        agent = SaaSEnhancedChartBotAgent(user)
        
        # Test basic query
        result = agent.process_query("What is my email address?")
        print(f"✅ Agent response: {result.get('success', False)}")
        print(f"   - Response: {result.get('response', 'N/A')[:100]}...")
        print(f"   - User role: {result.get('user_context', {}).get('role', 'N/A')}")
        print(f"   - Subscription: {result.get('user_context', {}).get('subscription_tier', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ SaaS agent error: {str(e)}")
        return False


def test_api_endpoint():
    """Test the API endpoint"""
    print("\n🔍 Testing API endpoint...")
    try:
        # Test if server is running
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("⚠️ Server responded with status:", response.status_code)
            return False
        
        # Test Chart Bot API
        api_response = requests.post(
            "http://127.0.0.1:8000/chart-bot-direct/api/direct/chat/",
            json={"message": "What is my email address?"},
            timeout=10
        )
        
        if api_response.status_code == 200:
            data = api_response.json()
            print(f"✅ API response successful: {data.get('success', False)}")
            print(f"   - Response: {data.get('response', 'N/A')[:100]}...")
            print(f"   - Session ID: {data.get('session_id', 'N/A')}")
            return True
        else:
            print(f"❌ API error: {api_response.status_code}")
            print(f"   - Response: {api_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
        return False
    except Exception as e:
        print(f"❌ API test error: {str(e)}")
        return False


def test_llm_connection():
    """Test LLM connection"""
    print("\n🔍 Testing LLM connection...")
    try:
        response = requests.get("http://125.18.84.108:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ LLM server is accessible")
            return True
        else:
            print(f"⚠️ LLM server responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ LLM connection error: {str(e)}")
        return False


def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🚀 Starting SaaS Chart Bot Comprehensive Verification")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("User Authentication", test_user_authentication),
        ("Data Fetcher", test_data_fetcher),
        ("Query Analyzer", test_query_analyzer),
        ("SaaS Agent", test_saas_agent),
        ("LLM Connection", test_llm_connection),
        ("API Endpoint", test_api_endpoint),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! SaaS Chart Bot is ready for production!")
    elif passed >= total * 0.8:
        print("⚠️ Most tests passed. Minor issues detected.")
    else:
        print("❌ Multiple test failures. Please review and fix issues.")
    
    return passed == total


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
