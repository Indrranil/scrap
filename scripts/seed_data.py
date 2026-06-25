#!/usr/bin/env python3
"""Seed admin, shopfloor plants, and shared scrapeyard for DigiScrapyard."""

import os
import sys
import time

from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth.jwt_auth import hash_password
from app.database.connection import SessionLocal
from app.models.employee_profile import EmployeeProfile
from app.models.plant import Plant
from app.models.scrapeyard import Scrapeyard
from app.services.auth import auth_service

PLANTS = [
    {"code": "UDE", "name": "UDE", "login_id": "UDE", "password": "1234", "qr_location": 3},
    {"code": "UTE", "name": "UTE", "login_id": "UTE", "password": "1234", "qr_location": 2},
    {"code": "U535", "name": "U535", "login_id": "U535", "password": "1234", "qr_location": 4},
]

SCRAPEYARD = {
    "name": "Central Scrapeyard",
    "login_id": "SCRAP",
    "password": "1234",
    "employees": ["Employee 1", "Employee 2"],
}


def _seed_plant(db, data: dict) -> None:
    existing = db.query(Plant).filter(Plant.login_id == data["login_id"]).first()
    if existing:
        print(f"  Plant {data['login_id']} already exists — skipped")
        return
    plant = Plant(
        code=data["code"],
        name=data["name"],
        login_id=data["login_id"],
        password_hash=hash_password(data["password"]),
        qr_location=data["qr_location"],
        is_active=True,
        created_at=int(time.time()),
    )
    db.add(plant)
    db.flush()
    for i in range(1, 5):
        db.add(
            EmployeeProfile(
                plant_id=plant.id,
                name=f"Employee {i}",
                is_active=True,
                created_at=int(time.time()),
            )
        )
    print(f"  Plant {data['login_id']} created (qr_location={data['qr_location']})")


def _seed_scrapeyard(db) -> None:
    existing = db.query(Scrapeyard).filter(Scrapeyard.login_id == SCRAPEYARD["login_id"]).first()
    if existing:
        print(f"  Scrapeyard {SCRAPEYARD['login_id']} already exists — skipped")
        return
    sy = Scrapeyard(
        name=SCRAPEYARD["name"],
        login_id=SCRAPEYARD["login_id"],
        password_hash=hash_password(SCRAPEYARD["password"]),
        is_active=True,
        created_at=int(time.time()),
    )
    db.add(sy)
    db.flush()
    for name in SCRAPEYARD["employees"]:
        db.add(
            EmployeeProfile(
                scrapeyard_id=sy.id,
                name=name,
                is_active=True,
                created_at=int(time.time()),
            )
        )
    print(f"  Scrapeyard {SCRAPEYARD['login_id']} created")


def main():
    db = SessionLocal()
    try:
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "Admin@123")
        name = os.getenv("ADMIN_NAME", "System Admin")
        try:
            auth_service.create_admin(db, username, password, name)
            print(f"Admin user created: {username}")
        except HTTPException as e:
            if e.status_code == 409:
                print(f"Admin user '{username}' already exists — skipped")
            else:
                raise

        print("Seeding plants...")
        for plant_data in PLANTS:
            _seed_plant(db, plant_data)

        print("Seeding scrapeyard...")
        _seed_scrapeyard(db)

        db.commit()
        print("Seed complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
