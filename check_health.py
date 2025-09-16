#!/usr/bin/env python3
"""
Check the health endpoint to see database connection details
"""
import requests

API_URL = "https://carpool-api-37218666122.us-central1.run.app"

def check_health():
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_health()
