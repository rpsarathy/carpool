#!/usr/bin/env python3
"""
Test script to verify PostgreSQL API functionality
"""

import os
import sys
import requests
import json
from pathlib import Path

# Set environment variable for database connection
os.environ["DATABASE_URL"] = "postgresql://carpool:Carpool%4080@104.154.101.239:5432/carpool_db"

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check: {data}")
            return data.get("database") == "healthy"
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_database_connection():
    """Test direct database connection"""
    try:
        from src.carpool.database import health_check
        result = health_check()
        if result:
            print("✅ Direct database connection successful")
        else:
            print("❌ Direct database connection failed")
        return result
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_groups_endpoint():
    """Test the groups endpoint"""
    try:
        response = requests.get("http://localhost:8000/groups")
        if response.status_code == 200:
            groups = response.json()
            print(f"✅ Groups endpoint: Found {len(groups)} groups")
            for group in groups:
                print(f"   - {group['name']}: {len(group['members'])} members")
            return True
        else:
            print(f"❌ Groups endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Groups endpoint error: {e}")
        return False

def test_on_demand_requests():
    """Test the on-demand requests endpoint"""
    try:
        response = requests.get("http://localhost:8000/on-demand/requests")
        if response.status_code == 200:
            data = response.json()
            requests_list = data.get("requests", [])
            print(f"✅ On-demand requests: Found {len(requests_list)} requests")
            return True
        else:
            print(f"❌ On-demand requests failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ On-demand requests error: {e}")
        return False

def test_drivers_endpoint():
    """Test the drivers endpoint"""
    try:
        response = requests.get("http://localhost:8000/on-demand/drivers")
        if response.status_code == 200:
            data = response.json()
            drivers = data.get("drivers", [])
            print(f"✅ Drivers endpoint: Found {len(drivers)} drivers")
            for driver in drivers:
                print(f"   - {driver}")
            return True
        else:
            print(f"❌ Drivers endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Drivers endpoint error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing PostgreSQL API functionality...")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Health Endpoint", test_health_endpoint),
        ("Groups Endpoint", test_groups_endpoint),
        ("On-demand Requests", test_on_demand_requests),
        ("Drivers Endpoint", test_drivers_endpoint),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print(f"\n📊 Test Results:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Summary: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! PostgreSQL migration is successful.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
