#!/usr/bin/env python3
"""
Quick API test to verify endpoints are working
"""
import os
import sys
import requests
import json
from pathlib import Path

# Set environment for local SQLite database
os.environ["DATABASE_URL"] = "sqlite:///./carpool_local.db"

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

BASE_URL = "http://localhost:8000"

def test_api():
    """Run basic API tests"""
    print("🚀 Starting API tests...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Make sure the server is running with: python start_server.py")
        return False
    
    # Test 2: Root endpoint
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test 3: Register user
    try:
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123!",
            "profile": {
                "full_name": "Test User"
            }
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code in [201, 409]:  # 201 created or 409 already exists
            print("✅ User registration working")
        else:
            print(f"❌ User registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ User registration error: {e}")
    
    # Test 4: Login user
    try:
        login_data = {
            "email": "test@example.com",
            "password": "TestPass123!"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ User login working")
        else:
            print(f"❌ User login failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ User login error: {e}")
    
    # Test 5: List groups
    try:
        response = requests.get(f"{BASE_URL}/groups")
        if response.status_code == 200:
            groups = response.json()
            print(f"✅ Groups endpoint working ({len(groups)} groups)")
        else:
            print(f"❌ Groups endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Groups endpoint error: {e}")
    
    # Test 6: Create group
    try:
        group_data = {
            "name": "Test Group",
            "origin": "Downtown",
            "destination": "Airport",
            "departure_time": "08:00",
            "days": ["Monday", "Wednesday", "Friday"],
            "driver": "Test Driver",
            "capacity": 4,
            "members": [
                {"name": "Test Driver", "email": "driver@example.com"},
                {"name": "Test Passenger", "email": "passenger@example.com"}
            ]
        }
        response = requests.post(f"{BASE_URL}/groups", json=group_data)
        if response.status_code in [201, 409]:  # 201 created or 409 already exists
            print("✅ Group creation working")
        else:
            print(f"❌ Group creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Group creation error: {e}")
    
    # Test 7: On-demand request
    try:
        request_data = {
            "user_email": "test@example.com",
            "origin": "Home",
            "destination": "Office",
            "date": "2024-01-15",
            "preferred_driver": "Test Driver"
        }
        response = requests.post(f"{BASE_URL}/on-demand/requests", json=request_data)
        if response.status_code == 200:
            print("✅ On-demand request working")
        else:
            print(f"❌ On-demand request failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ On-demand request error: {e}")
    
    print("\n🎉 API test completed!")
    return True

if __name__ == "__main__":
    test_api()
