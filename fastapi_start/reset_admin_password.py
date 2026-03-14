#!/usr/bin/env python3
"""
Reset admin password to admin / changeme123.
Run from Newbackend/fastapi_start with: python reset_admin_password.py
"""
import sys
from pathlib import Path

# Run from fastapi_start so app can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal
from app import models
from app.utils.security import hash_password

USERNAME = "admin"
PASSWORD = "changeme123"

def main():
    db = SessionLocal()
    try:
        admin = db.query(models.Admin).filter(models.Admin.username == USERNAME).first()
        new_hash = hash_password(PASSWORD)
        if admin:
            admin.password_hash = new_hash
            db.commit()
            print(f"Password for user '{USERNAME}' has been reset to '{PASSWORD}'.")
        else:
            db.add(models.Admin(username=USERNAME, password_hash=new_hash))
            db.commit()
            print(f"Admin user '{USERNAME}' created with password '{PASSWORD}'.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
