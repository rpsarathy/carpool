#!/usr/bin/env python3
"""
Test the production API to diagnose the 500 error
"""
import requests
import json

API_URL = "https://carpool-api-37218666122.us-central1.run.app"

def test_production_api():
    """Test production API endpoints to find the issue"""
    print("🔍 Testing production API...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        print(f"Health: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Health error: {e}")
    
    # Test root endpoint
    try:
        response = requests.get(f"{API_URL}/", timeout=10)
        print(f"Root: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Root error: {e}")
    
    # Test groups endpoint (the failing one)
    try:
        response = requests.get(f"{API_URL}/groups", timeout=10)
        print(f"Groups: {response.status_code} - {response.text}")
        if response.status_code != 200:
            print(f"Response headers: {dict(response.headers)}")
    except Exception as e:
        print(f"Groups error: {e}")
    
    # Test with CORS headers
    try:
        headers = {
            'Origin': 'https://carpool-web-dzxkfcfuiq-uc.a.run.app',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(f"{API_URL}/groups", headers=headers, timeout=10)
        print(f"CORS preflight: {response.status_code}")
        print(f"CORS headers: {dict(response.headers)}")
    except Exception as e:
        print(f"CORS preflight error: {e}")

if __name__ == "__main__":
    test_production_api()
