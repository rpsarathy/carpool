#!/usr/bin/env python3
"""
Comprehensive API test script for the carpool application
Tests all endpoints with various scenarios including success and error cases
"""

import os
import sys
import requests
import json
import time
from pathlib import Path
from datetime import datetime, date

# Set environment variable for database connection
os.environ["DATABASE_URL"] = "sqlite:///./carpool_local.db"

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.test_user_email = "test_user@example.com"
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append((test_name, success, details))
        print(f"{status}: {test_name}")
        if details and not success:
            print(f"    Details: {details}")
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            success = response.status_code == 200
            data = response.json() if success else {}
            details = f"Status: {response.status_code}, Response: {data}"
            self.log_test("Health Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Health Endpoint", False, str(e))
            return False
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            success = response.status_code == 200
            data = response.json() if success else {}
            details = f"Status: {response.status_code}, Response: {data}"
            self.log_test("Root Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Root Endpoint", False, str(e))
            return False
    
    def test_auth_register(self):
        """Test user registration"""
        try:
            payload = {
                "email": self.test_user_email,
                "password": "TestPass123!",
                "profile": {
                    "full_name": "Test User",
                    "phone": "555-1234"
                }
            }
            response = self.session.post(f"{self.base_url}/auth/register", json=payload)
            success = response.status_code in [201, 409]  # 409 if user already exists
            data = response.json() if response.status_code in [200, 201, 409] else {}
            details = f"Status: {response.status_code}, Response: {data}"
            self.log_test("Auth Register", success, details)
            return success
        except Exception as e:
            self.log_test("Auth Register", False, str(e))
            return False
    
    def test_auth_login(self):
        """Test user login"""
        try:
            payload = {
                "email": self.test_user_email,
                "password": "TestPass123!"
            }
            response = self.session.post(f"{self.base_url}/auth/login", json=payload)
            success = response.status_code == 200
            data = response.json() if success else {}
            details = f"Status: {response.status_code}, Response: {data}"
            self.log_test("Auth Login", success, details)
            return success
        except Exception as e:
            self.log_test("Auth Login", False, str(e))
            return False
    
    def test_auth_me(self):
        """Test get current user info"""
        try:
            headers = {"X-User-Email": self.test_user_email}
            response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
            success = response.status_code == 200
            data = response.json() if success else {}
            details = f"Status: {response.status_code}, Response: {data}"
            self.log_test("Auth Me", success, details)
            return success
        except Exception as e:
            self.log_test("Auth Me", False, str(e))
            return False
    
    def test_list_groups(self):
        """Test list all groups"""
        try:
            response = self.session.get(f"{self.base_url}/groups")
            success = response.status_code == 200
            data = response.json() if success else {}
            group_count = len(data) if isinstance(data, list) else 0
            details = f"Status: {response.status_code}, Groups found: {group_count}"
            self.log_test("List Groups", success, details)
            return success, data
        except Exception as e:
            self.log_test("List Groups", False, str(e))
            return False, []
    
    def test_get_group(self, group_name="NewPort Car Pool"):
        """Test get specific group"""
        try:
            response = self.session.get(f"{self.base_url}/groups/{group_name}")
            success = response.status_code == 200
            data = response.json() if success else {}
            details = f"Status: {response.status_code}, Group: {data.get('name', 'Not found')}"
            self.log_test(f"Get Group '{group_name}'", success, details)
            return success
        except Exception as e:
            self.log_test(f"Get Group '{group_name}'", False, str(e))
            return False
    
    def test_create_group(self):
        """Test create new group"""
        try:
            payload = {
                "name": f"Test Group {int(time.time())}",
                "origin": "Test Origin",
                "destination": "Test Destination",
                "departure_time": "09:00",
                "days": ["Monday", "Wednesday", "Friday"],
                "driver": "Test Driver",
                "capacity": 4,
                "members": [
                    {"name": "Test Member 1", "email": "member1@test.com"},
                    {"name": "Test Member 2", "email": "member2@test.com"}
                ]
            }
            response = self.session.post(f"{self.base_url}/groups", json=payload)
            success = response.status_code == 201
            data = response.json() if success else {}
            details = f"Status: {response.status_code}, Created: {data.get('name', 'Failed')}"
            self.log_test("Create Group", success, details)
            return success, data.get('name') if success else None
        except Exception as e:
            self.log_test("Create Group", False, str(e))
            return False, None
    
    def test_delete_group(self, group_name):
        """Test delete group"""
        if not group_name:
            self.log_test("Delete Group", False, "No group name provided")
            return False
        
        try:
            response = self.session.delete(f"{self.base_url}/groups/{group_name}")
            success = response.status_code == 204
            details = f"Status: {response.status_code}"
            self.log_test(f"Delete Group '{group_name}'", success, details)
            return success
        except Exception as e:
            self.log_test(f"Delete Group '{group_name}'", False, str(e))
            return False
    
    def test_create_on_demand_request(self):
        """Test create on-demand request"""
        try:
            payload = {
                "user_email": self.test_user_email,
                "origin": "Test Origin Location",
                "destination": "Test Destination Location",
                "date": "2025-01-15",
                "preferred_driver": "Test Driver"
            }
            response = self.session.post(f"{self.base_url}/on-demand/requests", json=payload)
            success = response.status_code == 200
            data = response.json() if success else {}
            details = f"Status: {response.status_code}, Response: {data}"
            self.log_test("Create On-demand Request", success, details)
            return success
        except Exception as e:
            self.log_test("Create On-demand Request", False, str(e))
            return False
    
    def test_get_on_demand_requests(self):
        """Test get all on-demand requests"""
        try:
            response = self.session.get(f"{self.base_url}/on-demand/requests")
            success = response.status_code == 200
            data = response.json() if success else {}
            request_count = len(data.get("requests", [])) if isinstance(data, dict) else 0
            details = f"Status: {response.status_code}, Requests found: {request_count}"
            self.log_test("Get On-demand Requests", success, details)
            return success
        except Exception as e:
            self.log_test("Get On-demand Requests", False, str(e))
            return False
    
    def test_get_drivers(self):
        """Test get available drivers"""
        try:
            response = self.session.get(f"{self.base_url}/on-demand/drivers")
            success = response.status_code == 200
            data = response.json() if success else {}
            driver_count = len(data.get("drivers", [])) if isinstance(data, dict) else 0
            details = f"Status: {response.status_code}, Drivers found: {driver_count}"
            self.log_test("Get Drivers", success, details)
            return success
        except Exception as e:
            self.log_test("Get Drivers", False, str(e))
            return False
    
    def test_admin_endpoints(self):
        """Test admin endpoints"""
        try:
            # Test list users
            response = self.session.get(f"{self.base_url}/admin/users")
            success = response.status_code == 200
            data = response.json() if success else {}
            user_count = len(data.get("users", [])) if isinstance(data, dict) else 0
            details = f"Status: {response.status_code}, Users found: {user_count}"
            self.log_test("Admin List Users", success, details)
            return success
        except Exception as e:
            self.log_test("Admin List Users", False, str(e))
            return False
    
    def test_error_cases(self):
        """Test various error scenarios"""
        tests_passed = 0
        total_tests = 0
        
        # Test 404 for non-existent group
        try:
            response = self.session.get(f"{self.base_url}/groups/NonExistentGroup")
            success = response.status_code == 404
            self.log_test("404 for Non-existent Group", success, f"Status: {response.status_code}")
            if success: tests_passed += 1
            total_tests += 1
        except Exception as e:
            self.log_test("404 for Non-existent Group", False, str(e))
            total_tests += 1
        
        # Test invalid auth (missing header)
        try:
            response = self.session.get(f"{self.base_url}/auth/me")
            success = response.status_code == 401
            self.log_test("401 for Missing Auth Header", success, f"Status: {response.status_code}")
            if success: tests_passed += 1
            total_tests += 1
        except Exception as e:
            self.log_test("401 for Missing Auth Header", False, str(e))
            total_tests += 1
        
        # Test invalid group creation (missing required fields)
        try:
            payload = {"name": "Incomplete Group"}  # Missing required fields
            response = self.session.post(f"{self.base_url}/groups", json=payload)
            success = response.status_code == 422
            self.log_test("422 for Invalid Group Data", success, f"Status: {response.status_code}")
            if success: tests_passed += 1
            total_tests += 1
        except Exception as e:
            self.log_test("422 for Invalid Group Data", False, str(e))
            total_tests += 1
        
        return tests_passed, total_tests
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🧪 Starting comprehensive API tests...")
        print(f"📋 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Basic endpoint tests
        self.test_health_endpoint()
        self.test_root_endpoint()
        
        # Authentication tests
        self.test_auth_register()
        self.test_auth_login()
        self.test_auth_me()
        
        # Group management tests
        success, groups = self.test_list_groups()
        if groups and len(groups) > 0:
            self.test_get_group(groups[0]['name'])
        
        # Test create and delete group
        created_success, group_name = self.test_create_group()
        if created_success and group_name:
            time.sleep(0.1)  # Small delay
            self.test_delete_group(group_name)
        
        # On-demand request tests
        self.test_create_on_demand_request()
        self.test_get_on_demand_requests()
        self.test_get_drivers()
        
        # Admin tests
        self.test_admin_endpoints()
        
        # Error case tests
        error_passed, error_total = self.test_error_cases()
        
        # Summary
        print("=" * 60)
        print("📊 Test Results Summary:")
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        for test_name, success, details in self.test_results:
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! API is working correctly.")
        else:
            print(f"⚠️  {total - passed} tests failed. Check the details above.")
        
        return passed == total

def main():
    """Main test function"""
    # Check if API server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API server not responding correctly at {BASE_URL}")
            print("   Please start the server with: uvicorn src.carpool.api:app --reload --port 8000")
            return False
    except requests.exceptions.RequestException:
        print(f"❌ Cannot connect to API server at {BASE_URL}")
        print("   Please start the server with: uvicorn src.carpool.api:app --reload --port 8000")
        return False
    
    # Run tests
    tester = APITester()
    success = tester.run_all_tests()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
