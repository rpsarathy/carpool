#!/usr/bin/env python3
"""
Test web app signup and login functionality
"""
import requests
import json
import time

# URLs
API_URL = "https://carpool-api-37218666122.us-central1.run.app"
WEB_URL = "https://carpool-web-dzxkfcfuiq-uc.a.run.app"

def test_api_endpoints():
    """Test API endpoints that the web app uses"""
    print("🔧 Testing API endpoints...")
    
    # Test health
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"✅ Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health error: {e}")
    
    # Test signup endpoint
    test_user = {
        "email": "webtest@example.com",
        "password": "TestPass123!",
        "profile": {
            "full_name": "Web Test User"
        }
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/signup", json=test_user)
        print(f"✅ Signup: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"❌ Signup error: {e}")
    
    # Test login endpoint
    login_data = {
        "email": "webtest@example.com",
        "password": "TestPass123!"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login", json=login_data)
        print(f"✅ Login: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"❌ Login error: {e}")
    
    # Test groups endpoint
    try:
        response = requests.get(f"{API_URL}/groups")
        print(f"✅ Groups: {response.status_code} - Found {len(response.json())} groups")
    except Exception as e:
        print(f"❌ Groups error: {e}")

def test_web_accessibility():
    """Test that web app is accessible"""
    print("\n🌐 Testing web app accessibility...")
    
    try:
        response = requests.get(WEB_URL, timeout=10)
        if response.status_code == 200:
            print(f"✅ Web app accessible at {WEB_URL}")
        else:
            print(f"❌ Web app returned {response.status_code}")
    except Exception as e:
        print(f"❌ Web app error: {e}")

def print_test_instructions():
    """Print manual testing instructions"""
    print(f"""
🧪 Manual Testing Instructions:

1. Open your web browser and go to:
   {WEB_URL}

2. Test Signup:
   - Click "Sign Up" or "Register" 
   - Fill in the form:
     * Email: test@example.com
     * Password: TestPass123!
     * Full Name: Test User
   - Click Submit
   - Should see success message or redirect to dashboard

3. Test Login:
   - If not already logged in, click "Login"
   - Use the same credentials:
     * Email: test@example.com  
     * Password: TestPass123!
   - Click Submit
   - Should see dashboard or main app interface

4. Test Groups:
   - Once logged in, navigate to Groups section
   - Should see list of carpool groups
   - Try creating a new group

5. Check Browser Console:
   - Press F12 to open Developer Tools
   - Check Console tab for any errors
   - Network tab should show successful API calls

API Endpoints for Reference:
- Health: {API_URL}/health
- Docs: {API_URL}/docs
- Signup: {API_URL}/auth/signup
- Login: {API_URL}/auth/login
- Groups: {API_URL}/groups
""")

if __name__ == "__main__":
    print("🚀 Testing Carpool Web App")
    print("=" * 50)
    
    test_api_endpoints()
    test_web_accessibility() 
    print_test_instructions()
