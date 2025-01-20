# test_endpoints.py
import requests
import json
from datetime import datetime

def get_fresh_token():
    url = "http://localhost:8080/realms/app-realm/protocol/openid-connect/token"
    payload = {
        "client_id": "fastapi-client",
        "client_secret": "bUvFqPkGPiP2F59KhslRGfUhCnTKtSvT",
        "grant_type": "password",
        "username": "chandani",
        "password": "chandani"
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Error getting token: {str(e)}")
        raise

def make_request(method, url, headers, json=None, params=None):
    try:
        response = requests.request(method, url, headers=headers, json=json, params=params)
        print(f"\n{method} {url}")
        if params:
            print(f"Query Params: {params}")
        if json:
            print(f"Request Body: {json}")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        return response
    except Exception as e:
        print(f"Request failed: {str(e)}")
        raise

def test_pipeline_session_endpoints():
    # Get a fresh token
    token = get_fresh_token()
    print(f"Got fresh token: {token[:30]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    base_url = "http://localhost:8000/v1/pipeline-session"
    
    # Test POST to create a new pipeline session without user param
    print("\nTesting POST /pipeline-session/new")
    create_data = {
        "pipeline_id": 1,
        "pipeline_input_id": 1,
        "name": "Test Pipeline Session",
        "created_by": 1,  # This will be overridden by authenticated user if user param not provided
        "is_usable": 1
    }
    response = make_request(
        "POST", 
        f"{base_url}/new",
        headers=headers, 
        json=create_data
    )
    
    # Test POST to create a new pipeline session with user param
    print("\nTesting POST /pipeline-session/new with user param")
    create_data_with_user = {
        "pipeline_id": 2,
        "pipeline_input_id": 2,
        "name": "Test Pipeline Session with User",
        "created_by": 1,
        "is_usable": 1
    }
    params = {"user": "test_user"}
    response_with_user = make_request(
        "POST", 
        f"{base_url}/new",
        headers=headers, 
        json=create_data_with_user,
        params=params
    )
    
    # If creation was successful, get the ID of the created session
    if response.status_code in [200, 201]:
        created_id = response.json()["id"]
        
        # Test GET specific pipeline session with overview=true
        print(f"\nTesting GET /pipeline-session/{created_id}")
        make_request(
            "GET", 
            f"{base_url}/{created_id}",
            headers=headers,
            params={"overview": True}
        )
        
        # Test GET specific pipeline session with overview=false
        print(f"\nTesting GET /pipeline-session/{created_id} with detailed view")
        make_request(
            "GET", 
            f"{base_url}/{created_id}",
            headers=headers,
            params={"overview": False}
        )
    
    # Test GET all pipeline sessions
    print("\nTesting GET /pipeline-session/all")
    make_request("GET", f"{base_url}/all", headers=headers)

if __name__ == "__main__":
    try:
        test_pipeline_session_endpoints()
    except Exception as e:
        print(f"Test failed: {str(e)}")