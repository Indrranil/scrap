import requests

def test_endpoints():
    # Get token
    token_response = requests.post(
        "http://localhost:8080/realms/app-realm/protocol/openid-connect/token",
        data={
            "client_id": "fastapi-client",
            "client_secret": "IRK0F8WoiZgBvOQtKHdXLG9Q9AjB602g",
            "grant_type": "password",
            "username": "chandani",
            "password": "chandani"
        }
    )
    token = token_response.json()["access_token"]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test endpoints
    base_url = "http://localhost:8000/v1/pipeline-session"
    
    # Create session (admin only)
    create_response = requests.post(
        f"{base_url}/new",
        headers=headers,
        json={
            "pipeline_id": 1,
            "pipeline_input_id": 1,
            "name": "Test Session"
        }
    )
    print("Create response:", create_response.status_code, create_response.text)
    
    # Get sessions (both roles)
    get_response = requests.get(
        f"{base_url}/",
        headers=headers
    )
    print("Get response:", get_response.status_code, get_response.text)

if __name__ == "__main__":
    test_endpoints()