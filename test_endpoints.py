# test_endpoints.py
import requests
import json

def get_fresh_token():
    url = "http://localhost:8080/realms/app-realm/protocol/openid-connect/token"
    payload = {
        "client_id": "fastapi-client",
        "client_secret": "lBgpLiCu6PoJTSjExg4GGu0fUGOPDV3a",
        "grant_type": "password",
        "username": "chandani",
        "password": "chandani123"
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Error getting token: {str(e)}")
        raise

def make_request(method, url, headers, json=None):
    try:
        response = requests.request(method, url, headers=headers, json=json)
        print(f"{method} {url}")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        return response
    except Exception as e:
        print(f"Request failed: {str(e)}")
        raise

def test_endpoints():
    # Get a fresh token
    token = get_fresh_token()
    print(f"Got fresh token: {token[:30]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    base_url = "http://localhost:8000"

    # Test POST to create a new pipeline
    print("\nTesting POST /pipelines/")
    create_data = {
        "name": "Test Pipeline",
        "is_usable": 1
    }
    response = make_request("POST", f"{base_url}/pipelines/", headers=headers, json=create_data)

    # If creation was successful, get the ID of the created pipeline
    if response.status_code == 200:
        created_id = response.json()["id"]
        
        # Test GET specific pipeline
        print(f"\nTesting GET /pipelines/{created_id}")
        make_request("GET", f"{base_url}/pipelines/{created_id}", headers=headers)

    # Test GET all pipelines
    print("\nTesting GET /pipelines/")
    make_request("GET", f"{base_url}/pipelines/", headers=headers)

if __name__ == "__main__":
    try:
        test_endpoints()
    except Exception as e:
        print(f"Test failed: {str(e)}")