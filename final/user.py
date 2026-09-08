# users.py
from werkzeug.security import generate_password_hash, check_password_hash

# Sample users: username -> hashed password
users = {
    "admin": generate_password_hash("admin123"),
    "student": generate_password_hash("student123")
}

def verify_user(username, password):
    if username in users:
        return check_password_hash(users[username], password)
    return False
