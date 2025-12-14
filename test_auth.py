import requests
import uuid

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    # 1. Register
    email = f"test_{uuid.uuid4()}@example.com"
    password = "password123"
    full_name = "Test User"
    
    print(f"Testing Registration for {email}...")
    reg_response = requests.post(f"{BASE_URL}/api/register", json={
        "email": email,
        "password": password,
        "full_name": full_name
    })
    
    if reg_response.status_code != 200:
        print(f"Registration failed: {reg_response.text}")
        return False
    print("Registration Successful")
    
    # 2. Login
    print("Testing Login...")
    login_response = requests.post(f"{BASE_URL}/api/token", data={
        "username": email,
        "password": password
    })
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return False
        
    token_data = login_response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        print("No access token returned")
        return False
    print("Login Successful, Token received")
    
    # 3. Protected Route
    print("Testing Protected Route (/api/users/me)...")
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
    
    if me_response.status_code != 200:
        print(f"Get Me failed: {me_response.text}")
        return False
        
    user_data = me_response.json()
    if user_data.get("email") != email:
        print(f"Email mismatch: expected {email}, got {user_data.get('email')}")
        return False
    
    print("Protected Route Verification Successful")
    return True

if __name__ == "__main__":
    try:
        success = test_auth_flow()
        if success:
            print("\n✅ All Auth Tests Passed!")
        else:
            print("\n❌ Tests Failed")
            exit(1)
    except Exception as e:
        print(f"Error running tests: {e}")
        print("Is the server running?")
        exit(1)
