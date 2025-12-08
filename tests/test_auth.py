#!/usr/bin/env python3
"""
Authentication System Test Script
Tests the complete auth flow: login, token validation, protected endpoints
"""

import requests
import json
from datetime import datetime

API_BASE = "http://127.0.0.1:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_health_check():
    """Test if API is running"""
    print_section("1. Health Check")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print(f"✅ API is running: {response.json()}")
            return True
        else:
            print(f"❌ API returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return False

def test_login():
    """Test login endpoint"""
    print_section("2. Login Test")
    try:
        # Test with correct credentials
        data = {
            "username": "admin",
            "password": "secret"
        }
        
        files = {
            "username": (None, "admin"),
            "password": (None, "secret")
        }
        
        response = requests.post(f"{API_BASE}/token", data=files)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"✅ Login successful!")
            print(f"   Token: {access_token[:20]}...{access_token[-20:]}")
            print(f"   Type: {token_data.get('token_type')}")
            return access_token
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_invalid_login():
    """Test login with wrong password"""
    print_section("3. Invalid Login Test")
    try:
        files = {
            "username": (None, "admin"),
            "password": (None, "wrongpassword")
        }
        
        response = requests.post(f"{API_BASE}/token", data=files)
        
        if response.status_code == 401:
            print(f"✅ Correctly rejected invalid credentials")
            print(f"   Error: {response.json().get('detail')}")
            return True
        else:
            print(f"❌ Should have returned 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_protected_endpoint(token):
    """Test access to protected endpoint with token"""
    print_section("4. Protected Endpoint Test (With Token)")
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(f"{API_BASE}/inventory/", headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Successfully accessed protected endpoint")
            data = response.json()
            print(f"   Inventory items: {len(data) if isinstance(data, list) else 'N/A'}")
            return True
        else:
            print(f"❌ Failed to access protected endpoint: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_protected_endpoint_no_auth():
    """Test access to protected endpoint without token"""
    print_section("5. Protected Endpoint Test (Without Token)")
    try:
        response = requests.get(f"{API_BASE}/inventory/")
        
        if response.status_code == 403:
            print(f"✅ Correctly rejected request without token")
            return True
        elif response.status_code == 401:
            print(f"✅ Correctly rejected request without token (401)")
            return True
        else:
            print(f"❌ Should have rejected, got {response.status_code}")
            print(f"   Response: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_invalid_token():
    """Test access with invalid token"""
    print_section("6. Invalid Token Test")
    try:
        headers = {
            "Authorization": "Bearer invalid.token.here"
        }
        
        response = requests.get(f"{API_BASE}/inventory/", headers=headers)
        
        if response.status_code == 401:
            print(f"✅ Correctly rejected invalid token")
            print(f"   Error: {response.json().get('detail')}")
            return True
        else:
            print(f"❌ Should have returned 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_agent_endpoints(token):
    """Test agent endpoints with authentication"""
    print_section("7. Agent Endpoints (With Token)")
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # Test /agent/jobs
        response = requests.get(f"{API_BASE}/agent/jobs", headers=headers)
        if response.status_code == 200:
            print(f"✅ /agent/jobs accessible")
            data = response.json()
            print(f"   Total jobs: {data.get('total', 'N/A')}")
        else:
            print(f"❌ /agent/jobs failed: {response.status_code}")
        
        # Test /agent/run_once (will start a job)
        response = requests.post(f"{API_BASE}/agent/run_once", headers=headers)
        if response.status_code == 200:
            print(f"✅ /agent/run_once accessible (job started)")
            data = response.json()
            print(f"   Job ID: {data.get('job_id')}")
            return True
        else:
            print(f"❌ /agent/run_once failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  AUTHENTICATION SYSTEM TEST SUITE")
    print("  Testing JWT-based auth implementation")
    print("="*60)
    
    results = []
    
    # Run tests
    if not test_health_check():
        print("\n❌ API is not running. Please start the backend server.")
        return
    
    results.append(("Health Check", test_health_check()))
    results.append(("Invalid Login", test_invalid_login()))
    
    token = test_login()
    results.append(("Login", token is not None))
    
    if token:
        results.append(("Protected Endpoint (with token)", test_protected_endpoint(token)))
        results.append(("Agent Endpoints", test_agent_endpoints(token)))
    
    results.append(("Protected Endpoint (no token)", test_protected_endpoint_no_auth()))
    results.append(("Invalid Token", test_invalid_token()))
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All authentication tests passed! Auth system is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")

if __name__ == "__main__":
    main()
