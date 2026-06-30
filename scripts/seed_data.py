#!/usr/bin/env python3
"""Seed admin, shopfloor plants, shared scrapeyard, security, and per-plant GSO."""

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
from app.models.gso import Gso
from app.models.plant import Plant
from app.models.scrapeyard import Scrapeyard
from app.models.security import Security
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

SECURITY = {
    "name": "Security Gate",
    "login_id": "Security-1",
    "password": "1234",
    "employees": ["Employee 1", "Employee 2", "Employee 3", "Employee 4"],
}

GSO_EMPLOYEES = ["Employee 1", "Employee 2", "Employee 3", "Employee 4"]


def _seed_plant(db, data: dict) -> Plant:
    existing = db.query(Plant).filter(Plant.login_id == data["login_id"]).first()
    if existing:
        print(f"  Plant {data['login_id']} already exists — skipped")
        return existing
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
    return plant


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


def _seed_security(db) -> None:
    existing = db.query(Security).filter(Security.login_id == SECURITY["login_id"]).first()
    if existing:
        print(f"  Security {SECURITY['login_id']} already exists — skipped")
        return
    sec = Security(
        name=SECURITY["name"],
        login_id=SECURITY["login_id"],
        password_hash=hash_password(SECURITY["password"]),
        is_active=True,
        created_at=int(time.time()),
    )
    db.add(sec)
    db.flush()
    for name in SECURITY["employees"]:
        db.add(
            EmployeeProfile(
                security_id=sec.id,
                name=name,
                is_active=True,
                created_at=int(time.time()),
            )
        )
    print(f"  Security {SECURITY['login_id']} created")


def _seed_gso_for_plant(db, plant: Plant) -> None:
    login_id = f"GSO-{plant.login_id}"
    existing = db.query(Gso).filter(Gso.login_id == login_id).first()
    if existing:
        if not existing.plant_id:
            existing.plant_id = plant.id
        print(f"  GSO {login_id} already exists — skipped")
        return
    gso = Gso(
        plant_id=plant.id,
        name=f"GSO {plant.name}",
        login_id=login_id,
        password_hash=hash_password("1234"),
        is_active=True,
        created_at=int(time.time()),
    )
    db.add(gso)
    db.flush()
    for name in GSO_EMPLOYEES:
        db.add(
            EmployeeProfile(
                gso_id=gso.id,
                name=name,
                is_active=True,
                created_at=int(time.time()),
            )
        )
    print(f"  GSO {login_id} created for plant {plant.login_id}")


def _migrate_legacy_gso(db) -> None:
    legacy = db.query(Gso).filter(Gso.login_id == "GSO").first()
    if not legacy:
        return
    ude = db.query(Plant).filter(Plant.login_id == "UDE").first()
    if ude and not legacy.plant_id:
        legacy.plant_id = ude.id
        legacy.login_id = "GSO-UDE"
        print("  Migrated legacy GSO login to GSO-UDE with plant UDE")


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
        plants = []
        for plant_data in PLANTS:
            plants.append(_seed_plant(db, plant_data))

        print("Seeding scrapeyard...")
        _seed_scrapeyard(db)

        print("Seeding security...")
        _seed_security(db)

        print("Seeding per-plant GSO...")
        _migrate_legacy_gso(db)
        for plant in plants:
            _seed_gso_for_plant(db, plant)

        db.commit()
        print("Seed complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
