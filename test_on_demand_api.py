#!/usr/bin/env python3
"""
Test the on-demand API endpoints directly
"""
import requests
import json

API_URL = "https://carpool-api-37218666122.us-central1.run.app"

def test_on_demand_create():
    """Test creating an on-demand request"""
    print("🚗 Testing on-demand request creation...")
    
    # Test payload
    payload = {
        "user_email": "test@example.com",
        "origin": "Downtown",
        "destination": "Airport",
        "date": "2024-01-15",
        "preferred_driver": "John Doe"
    }
    
    try:
        response = requests.post(f"{API_URL}/on_demand/requests", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 422:
            print("❌ 422 Validation Error - checking response details...")
            try:
                error_detail = response.json()
                print(f"Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
        elif response.status_code == 201 or response.status_code == 200:
            print("✅ On-demand request created successfully")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_on_demand_get():
    """Test getting on-demand requests"""
    print("\n📋 Testing get on-demand requests...")
    
    try:
        response = requests.get(f"{API_URL}/on_demand/requests")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data.get('requests', []))} on-demand requests")
        else:
            print(f"❌ Failed to get requests: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_on_demand_drivers():
    """Test getting available drivers"""
    print("\n👥 Testing get available drivers...")
    
    try:
        response = requests.get(f"{API_URL}/on_demand/drivers")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data.get('drivers', []))} available drivers")
        else:
            print(f"❌ Failed to get drivers: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_minimal_payload():
    """Test with minimal required payload"""
    print("\n🔬 Testing with minimal payload...")
    
    payload = {
        "user_email": "minimal@test.com",
        "origin": "A",
        "destination": "B", 
        "date": "2024-01-01"
    }
    
    try:
        response = requests.post(f"{API_URL}/on_demand/requests", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ Minimal payload works")
        else:
            print("❌ Minimal payload failed")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_empty_payload():
    """Test with empty payload to see validation errors"""
    print("\n🚫 Testing with empty payload...")
    
    try:
        response = requests.post(f"{API_URL}/on_demand/requests", json={})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing On-Demand API Endpoints")
    print("=" * 50)
    
    test_on_demand_create()
    test_minimal_payload()
    test_empty_payload()
    test_on_demand_get()
    test_on_demand_drivers()
    
    print("\n🎯 On-demand API testing completed!")
