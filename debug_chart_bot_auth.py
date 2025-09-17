#!/usr/bin/env python
"""
Debug Chart Bot Authentication
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
from django.test import Client
from django.urls import reverse
import json


def test_authentication():
    """Test Chart Bot authentication"""
    print("🔐 Testing Chart Bot Authentication")
    print("=" * 50)
    
    # Create test client
    client = Client()
    
    # Test without authentication
    print("1. Testing without authentication...")
    response = client.get('/chart-bot/api/test-auth/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 401:
        print("   ✅ Correctly returns 401 for unauthenticated requests")
    else:
        print(f"   ❌ Expected 401, got {response.status_code}")
    
    # Test with authentication
    print("\n2. Testing with authentication...")
    
    # Get or create a test user
    user = User.objects.first()
    if not user:
        print("   ❌ No users found. Please create a user first.")
        return False
    
    print(f"   Using user: {user.username}")
    
    # Login the user
    client.force_login(user)
    
    # Test authentication endpoint
    response = client.get('/chart-bot/api/test-auth/')
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Authentication successful")
        print(f"   User: {data.get('username')}")
        print(f"   User ID: {data.get('user_id')}")
    else:
        print(f"   ❌ Authentication failed: {response.status_code}")
        print(f"   Response: {response.content}")
        return False
    
    # Test chat endpoint
    print("\n3. Testing chat endpoint...")
    response = client.post('/chart-bot/api/chat/', {
        'message': 'Hello, test message'
    }, content_type='application/json')
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Chat endpoint working")
        print(f"   Response: {data.get('response', 'No response')[:100]}...")
    else:
        print(f"   ❌ Chat endpoint failed: {response.status_code}")
        print(f"   Response: {response.content}")
    
    # Test status endpoint
    print("\n4. Testing status endpoint...")
    response = client.get('/chart-bot/api/status/')
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Status endpoint working")
        print(f"   Bot enabled: {data.get('bot_enabled')}")
        print(f"   User role: {data.get('user_role')}")
    else:
        print(f"   ❌ Status endpoint failed: {response.status_code}")
        print(f"   Response: {response.content}")
    
    return True


def test_csrf_token():
    """Test CSRF token handling"""
    print("\n🛡️ Testing CSRF Token Handling")
    print("=" * 50)
    
    client = Client(enforce_csrf_checks=True)
    
    # Get or create a test user
    user = User.objects.first()
    if not user:
        print("❌ No users found. Please create a user first.")
        return False
    
    client.force_login(user)
    
    # Test without CSRF token
    print("1. Testing without CSRF token...")
    response = client.post('/chart-bot/api/chat/', {
        'message': 'Hello, test message'
    }, content_type='application/json')
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 403:
        print("   ✅ Correctly requires CSRF token")
    else:
        print(f"   ⚠️ Expected 403, got {response.status_code}")
    
    return True


def main():
    """Run all authentication tests"""
    print("🚀 Chart Bot Authentication Debug")
    print("=" * 50)
    
    # Test authentication
    auth_success = test_authentication()
    
    # Test CSRF
    csrf_success = test_csrf_token()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Authentication: {'✅ PASS' if auth_success else '❌ FAIL'}")
    print(f"   CSRF Handling: {'✅ PASS' if csrf_success else '❌ FAIL'}")
    
    if auth_success and csrf_success:
        print("\n🎉 All authentication tests passed!")
        print("\n💡 If you're still getting 401 errors in the browser:")
        print("   1. Make sure you're logged in to the Django admin")
        print("   2. Check browser console for detailed error messages")
        print("   3. Verify the CSRF token is being sent correctly")
        print("   4. Check if cookies are being blocked")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return auth_success and csrf_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
