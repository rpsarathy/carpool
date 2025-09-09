#!/usr/bin/env python3
"""
Test script for GCP Carpool API - Signup and Login endpoints
Usage: python test_gcp_api.py
"""

import requests
import json
import time
from datetime import datetime

# GCP API Base URL
API_BASE = "https://carpool-api-37218666122.us-central1.run.app"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_signup(email, password, profile=None):
    """Test the signup endpoint"""
    print(f"\n🔍 Testing signup for {email}...")
    
    payload = {
        "email": email,
        "password": password
    }
    
    if profile:
        payload["profile"] = profile
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/signup",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Signup successful")
            return True, response.json()
        elif response.status_code == 422:
            print("❌ Signup failed - Validation error")
            return False, response.json()
        else:
            print(f"❌ Signup failed - Status: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return False, None

def test_login(email, password):
    """Test the login endpoint"""
    print(f"\n🔍 Testing login for {email}...")
    
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login successful")
            return True, response.json()
        elif response.status_code == 401:
            print("❌ Login failed - Invalid credentials")
            return False, response.json()
        else:
            print(f"❌ Login failed - Status: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False, None

def test_me_endpoint(email):
    """Test the /auth/me endpoint"""
    print(f"\n🔍 Testing /auth/me for {email}...")
    
    try:
        response = requests.get(
            f"{API_BASE}/auth/me",
            headers={"X-User-Email": email}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ /auth/me successful")
            return True, response.json()
        else:
            print(f"❌ /auth/me failed - Status: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ /auth/me error: {e}")
        return False, None

def test_db_state():
    """Test the debug database state endpoint"""
    print(f"\n🔍 Testing database state...")
    
    try:
        response = requests.get(f"{API_BASE}/debug/db-state")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Database state check successful")
            return True, response.json()
        else:
            print(f"❌ Database state check failed - Status: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Database state error: {e}")
        return False, None

def main():
    """Run all tests"""
    print("🚀 Starting GCP Carpool API Tests")
    print(f"API Base URL: {API_BASE}")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("❌ Health check failed, stopping tests")
        return
    
    # Test database state
    test_db_state()
    
    # Generate unique test email
    timestamp = int(time.time())
    test_email = f"test{timestamp}@example.com"
    test_password = "TestPass123!"
    
    # Test profile data
    test_profile = {
        "full_name": "Test User",
        "phone": "+1234567890",
        "date_of_birth": "1990-01-01",
        "gender": "Other",
        "address": {
            "city": "Test City",
            "state": "CA",
            "zip": "12345"
        }
    }
    
    print(f"\n📧 Using test email: {test_email}")
    
    # Test signup
    signup_success, signup_data = test_signup(test_email, test_password, test_profile)
    
    if signup_success:
        # Test login with correct credentials
        login_success, login_data = test_login(test_email, test_password)
        
        if login_success:
            # Test /auth/me endpoint
            test_me_endpoint(test_email)
        
        # Test login with wrong password
        print(f"\n🔍 Testing login with wrong password...")
        test_login(test_email, "WrongPassword123!")
    
    # Test signup with duplicate email
    print(f"\n🔍 Testing duplicate signup...")
    test_signup(test_email, test_password)
    
    # Test signup with invalid email
    print(f"\n🔍 Testing invalid email signup...")
    test_signup("invalid-email", test_password)
    
    # Test signup with weak password
    print(f"\n🔍 Testing weak password signup...")
    test_signup(f"weak{timestamp}@example.com", "weak")
    
    print("\n" + "=" * 50)
    print("🏁 Tests completed!")

if __name__ == "__main__":
    main()
