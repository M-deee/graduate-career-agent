import requests
import uuid
import time

BASE_URL = "http://localhost:8000"

def test_persistent_chat():
    print("Testing Persistent Chat...")
    
    # 1. Register User
    email = f"chat_test_{uuid.uuid4()}@example.com"
    password = "password123"
    print(f"Registering {email}...")
    requests.post(f"{BASE_URL}/api/register", json={
        "email": email,
        "password": password,
        "full_name": "Chat Tester"
    })
    
    # 2. Login
    login_resp = requests.post(f"{BASE_URL}/api/token", data={
        "username": email,
        "password": password
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Send Message 1
    msg1 = "My name is Alice."
    print(f"Sending: {msg1}")
    resp1 = requests.post(f"{BASE_URL}/api/chat", json={"message": msg1}, headers=headers)
    print(f"Response: {resp1.json().get('response')}")
    
    # 4. Send Message 2 (Follow-up)
    # The agent should remember the name from the DB history
    msg2 = "What is my name?"
    print(f"Sending: {msg2}")
    resp2 = requests.post(f"{BASE_URL}/api/chat", json={"message": msg2}, headers=headers)
    answer = resp2.json().get('response')
    print(f"Response: {answer}")
    
    if "Alice" in answer:
        print("✅ SUCCESS: Agent remembered the name from history!")
        return True
    else:
        print("❌ FAILURE: Agent did not remember the name.")
        return False

if __name__ == "__main__":
    try:
        success = test_persistent_chat()
        if not success:
            exit(1)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
