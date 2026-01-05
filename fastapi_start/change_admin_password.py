#!/usr/bin/env python3
"""
Script to change the admin password in the database.
"""
import os
import sys
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models
from app.database import Base

# Database setup
DATABASE_URL = "sqlite:///./products.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_salt() -> str:
    return os.getenv("ADMIN_PASSWORD_SALT", "static-salt")

def hash_password(password: str) -> str:
    salt = get_salt()
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()

def change_admin_password(username: str, new_password: str):
    """Change admin password in the database."""
    db = SessionLocal()
    try:
        admin = db.query(models.Admin).filter(models.Admin.username == username).first()
        
        if not admin:
            print(f"Error: Admin user '{username}' not found in database.")
            return False
        
        # Hash the new password
        password_hash = hash_password(new_password)
        admin.password_hash = password_hash
        db.commit()
        
        print(f"✓ Successfully changed password for admin user '{username}'")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python change_admin_password.py <new_password>")
        print("Example: python change_admin_password.py myNewPassword123")
        sys.exit(1)
    
    new_password = sys.argv[1]
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    
    if change_admin_password(admin_username, new_password):
        print(f"Admin password for '{admin_username}' has been updated.")
        sys.exit(0)
    else:
        sys.exit(1)
