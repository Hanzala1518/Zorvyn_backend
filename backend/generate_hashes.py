"""
Run this script once to generate real bcrypt hashes for demo users.
Then paste the printed UPDATE statements into Supabase SQL Editor.

Usage:
    cd backend
    python generate_hashes.py
"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEMO_USERS = [
    ("admin@demo.com", "admin123"),
    ("analyst@demo.com", "analyst123"),
    ("viewer@demo.com", "viewer123"),
]

print("-- Run these UPDATE statements in Supabase SQL Editor:")
print()
for email, password in DEMO_USERS:
    hashed = pwd_context.hash(password)
    print(f"UPDATE users SET password_hash = '{hashed}' WHERE email = '{email}';")
print()
print("-- Done. Each hash is unique and secure.")
