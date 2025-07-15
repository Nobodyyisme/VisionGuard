import requests

BASE_URL = "http://localhost:5000"

# 🔐 AUTH
def login_user(username, password):
    url = f"{BASE_URL}/auth/login"
    res = requests.post(url, json={"username": username, "password": password})
    return res.json() if res.ok else None

def register_user(token, data):
    url = f"{BASE_URL}/auth/register"
    headers = {
        "Authorization": f"Bearer {token}",  
        "Content-Type": "application/json"   
    }
    return requests.post(url, json=data, headers=headers)

# 👤 EMPLOYEE
def mark_own_attendance(token, status):
    url = f"{BASE_URL}/employee/attendance/self"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.post(url, json={"status": status}, headers=headers)

def get_own_attendance(token):
    url = f"{BASE_URL}/employee/attendance/self"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers).json()

# 🧑‍💼 ADMIN & HR
def get_all_attendance(token):
    url = f"{BASE_URL}/attendance/attendance"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers).json()

def mark_attendance_any(token, data):
    url = f"{BASE_URL}/attendance/attendance"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.post(url, json=data, headers=headers)

def get_all_users(token):
    url = f"{BASE_URL}/attendance/users"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers).json()

def get_user_attendance(token, user_id):
    url = f"{BASE_URL}/attendance/attendance/user/{user_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers).json()

# 🤖 MODEL (optional)
def mark_by_model(employee_id, status="Present"):
    url = f"{BASE_URL}/attendance/attendance/mark/{employee_id}"
    return requests.post(url, json={"status": status})

def get_my_info(token):
    url = f"{BASE_URL}/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(url, headers=headers)
    return res.json() if res.ok else None
