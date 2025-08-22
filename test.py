# test_api_requests.py
import requests

BASE_URL = "http://localhost:8000"  # Change if your server runs elsewhere
EMAIL = "satyampathak67@gmail.com"
PHONE_NUMBER = "+916388494727"  # Replace with your actual number
PASSWORD = "testpass123"

# --- 1. Register User ---
def register_user():
    data = {
        "name": "Satyam",
        "email": EMAIL,
        "phone": PHONE_NUMBER,
        "password": PASSWORD,
        "reminder_type": "both",
        "prescriptions": [
            {
                "medicine_name": "Paracetamol",
                "dosage": "500mg",
                "timings": "09:00,14:00,21:00"
            }
        ]
    }
    resp = requests.post(f"{BASE_URL}/users/", json=data)
    print("Register User:", resp.status_code, resp.json())
    assert resp.status_code == 200

# --- 2. Login ---
def login_user():
    data = {"username": EMAIL, "password": PASSWORD}
    resp = requests.post(f"{BASE_URL}/token", data=data)
    print("Login:", resp.status_code, resp.json())
    assert resp.status_code == 200
    return resp.json()["access_token"]

# --- 3. Add Prescription ---
def add_prescription(token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "medicine_name": "Ibuprofen",
        "dosage": "200mg",
        "timings": "08:00,20:00"
    }
    resp = requests.post(f"{BASE_URL}/prescriptions/add", json=data, headers=headers)
    print("Add Prescription:", resp.status_code, resp.json())
    assert resp.status_code == 200

# --- 4. Add User Text ---
def add_user_text(token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"text": "I have put the high school marksheet in the almirah locker."}
    resp = requests.post(f"{BASE_URL}/user/text", json=data, headers=headers)
    print("Add User Text:", resp.status_code, resp.json())
    assert resp.status_code == 200

# --- 5. Ask AI (Gemini) ---
def ask_ai(token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"question": "Where did I keep my marksheet?"}
    resp = requests.post(f"{BASE_URL}/user/ask", json=data, headers=headers)
    print("Ask AI:", resp.status_code, resp.json())
    assert resp.status_code == 200

# --- 6. Test Call ---
def test_call():
    data = {
        "phone": PHONE_NUMBER,
        "msg": "This is a test call from Medicine Reminder system."
    }
    resp = requests.post(f"{BASE_URL}/test/call", json=data)  # use json=data
    print("Test Call:", resp.status_code, resp.json())
    assert resp.status_code == 200

# --- 7. Test Email ---

def test_email():
    data = {
        "email": EMAIL,
        "message": "This is a test email from Medicine Reminder system."
    }
    resp = requests.post(f"{BASE_URL}/test/email", json=data)  # send as JSON
    print("Test Email:", resp.status_code, resp.json())
    assert resp.status_code == 200


# --- Run all tests ---
if __name__ == "__main__":
    register_user()
    token = login_user()
    add_prescription(token)
    add_user_text(token)
    ask_ai(token)
    test_call()
    test_email()
