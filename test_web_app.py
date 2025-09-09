#!/usr/bin/env python3
"""
Test script to verify web app configuration and simulate web app signup/login flow
Usage: python test_web_app.py
"""

import requests
import json
import time
import os

def check_web_app_config():
    """Check if web app is configured to use the correct API endpoint"""
    print("🔍 Checking web app configuration...")
    
    # Check if VITE_API_BASE environment variable is set
    vite_api_base = os.environ.get('VITE_API_BASE')
    if vite_api_base:
        print(f"✅ VITE_API_BASE environment variable: {vite_api_base}")
        return vite_api_base
    else:
        print("⚠️  VITE_API_BASE not set, will use default: http://localhost:8000")
        return "http://localhost:8000"

def simulate_web_app_signup():
    """Simulate the web app signup flow"""
    print("\n🔍 Simulating web app signup flow...")
    
    # Use the GCP API endpoint (what the deployed web app should use)
    api_base = "https://carpool-api-37218666122.us-central1.run.app"
    
    # Generate unique test data
    timestamp = int(time.time())
    test_email = f"webapp{timestamp}@example.com"
    test_password = "WebApp123!"
    
    # Simulate web app signup request
    signup_payload = {
        "email": test_email,
        "password": test_password,
        "profile": {
            "full_name": "Web App Test User",
            "phone": "+1987654321",
            "date_of_birth": "1985-05-15",
            "gender": "Other",
            "address": {
                "city": "San Francisco",
                "state": "CA",
                "zip": "94105"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{api_base}/auth/signup",
            headers={
                "Content-Type": "application/json",
                "Origin": "https://carpool-web-37218666122.us-central1.run.app",  # Simulate web app origin
                "Referer": "https://carpool-web-37218666122.us-central1.run.app/signup"
            },
            json=signup_payload
        )
        
        print(f"Signup Status: {response.status_code}")
        print(f"Signup Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Web app signup simulation successful")
            return test_email, test_password
        else:
            print("❌ Web app signup simulation failed")
            return None, None
            
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return None, None

def simulate_web_app_login(email, password):
    """Simulate the web app login flow"""
    print(f"\n🔍 Simulating web app login for {email}...")
    
    api_base = "https://carpool-api-37218666122.us-central1.run.app"
    
    login_payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{api_base}/auth/login",
            headers={
                "Content-Type": "application/json",
                "Origin": "https://carpool-web-37218666122.us-central1.run.app",
                "Referer": "https://carpool-web-37218666122.us-central1.run.app/login"
            },
            json=login_payload
        )
        
        print(f"Login Status: {response.status_code}")
        print(f"Login Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Web app login simulation successful")
            
            # Test the /auth/me endpoint (what web app does after login)
            me_response = requests.get(
                f"{api_base}/auth/me",
                headers={
                    "X-User-Email": email,
                    "Origin": "https://carpool-web-37218666122.us-central1.run.app"
                }
            )
            
            print(f"Profile fetch status: {me_response.status_code}")
            if me_response.status_code == 200:
                profile_data = me_response.json()
                print(f"✅ Profile retrieved: {profile_data.get('profile', {}).get('full_name', 'No name')}")
            
            return True
        else:
            print("❌ Web app login simulation failed")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

def test_cors_headers():
    """Test CORS headers for web app domains"""
    print("\n🔍 Testing CORS headers...")
    
    api_base = "https://carpool-api-37218666122.us-central1.run.app"
    
    # Test OPTIONS request (preflight)
    try:
        response = requests.options(
            f"{api_base}/auth/login",
            headers={
                "Origin": "https://carpool-web-37218666122.us-central1.run.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        print(f"CORS preflight status: {response.status_code}")
        cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        print(f"CORS headers: {cors_headers}")
        
        if response.status_code in [200, 204]:
            print("✅ CORS preflight successful")
        else:
            print("⚠️  CORS preflight may have issues")
            
    except Exception as e:
        print(f"❌ CORS test error: {e}")

def main():
    """Run web app tests"""
    print("🚀 Starting Web App Integration Tests")
    print("=" * 50)
    
    # Check configuration
    check_web_app_config()
    
    # Test CORS
    test_cors_headers()
    
    # Test signup flow
    email, password = simulate_web_app_signup()
    
    if email and password:
        # Test login flow
        simulate_web_app_login(email, password)
    
    print("\n" + "=" * 50)
    print("🏁 Web app tests completed!")
    print("\n📝 Next steps:")
    print("1. Open your web app: https://carpool-web-37218666122.us-central1.run.app")
    print("2. Try signing up with a new account")
    print("3. Try logging in with the account")
    print("4. Check browser console for any errors")

if __name__ == "__main__":
    main()
