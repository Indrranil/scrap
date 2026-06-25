#!/usr/bin/env python3
"""Seed initial admin user for DigiScrapyard."""

import os
import sys

from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import SessionLocal
from app.services.auth import auth_service


def main():
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "Admin@123")
    name = os.getenv("ADMIN_NAME", "System Admin")

    db = SessionLocal()
    try:
        admin = auth_service.create_admin(db, username, password, name)
        print(f"Admin user created: {admin.username} (id={admin.id})")
    except HTTPException as e:
        if e.status_code == 409:
            print(f"Admin user '{username}' already exists")
        else:
            raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
