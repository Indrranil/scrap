import time

from app.auth.jwt_auth import hash_password
from app.models.employee_profile import EmployeeProfile
from app.models.enums import AppRole
from app.models.plant import Plant
from app.services.auth import auth_service

from app.auto_tests.conftest import SAMPLE_QR


def _create_plant(db, role, login_id, linked_id=None):
    plant = Plant(
        code="UDE",
        name=f"Test {role.value}",
        login_id=login_id,
        password_hash=hash_password("password123"),
        app_role=role,
        linked_scrapeyard_plant_id=linked_id,
        is_active=True,
        created_at=int(time.time()),
    )
    db.add(plant)
    db.flush()
    emp = EmployeeProfile(
        plant_id=plant.id,
        name="Rohan",
        is_active=True,
        created_at=int(time.time()),
    )
    db.add(emp)
    db.commit()
    db.refresh(plant)
    db.refresh(emp)
    return plant, emp


def test_full_lifecycle_dispatch_accept(client, db_session):
    admin = auth_service.create_admin(db_session, "admin", "adminpass", "Admin")
    sy_plant, sy_emp = _create_plant(
        db_session, AppRole.SCRAPEYARD, "sy-plant"
    )
    sf_plant, sf_emp = _create_plant(
        db_session,
        AppRole.SHOPFLOOR,
        "sf-plant",
        linked_id=sy_plant.id,
    )

    sf_login = client.post(
        "/v1/auth/login",
        json={"login_id": "sf-plant", "password": "password123"},
    )
    assert sf_login.status_code == 200
    sf_token = sf_login.json()["access_token"]

    dispatch = client.post(
        "/v1/shopfloor/dispatch",
        headers={"Authorization": f"Bearer {sf_token}"},
        json={
            "qr_raw": SAMPLE_QR,
            "gp_number": "125",
            "employee_id": sf_emp.id,
        },
    )
    assert dispatch.status_code == 200
    transfer_id = dispatch.json()["id"]
    assert dispatch.json()["status"] == "dispatched"

    sy_login = client.post(
        "/v1/auth/login",
        json={"login_id": "sy-plant", "password": "password123"},
    )
    sy_token = sy_login.json()["access_token"]

    accept = client.post(
        "/v1/scrapeyard/accept",
        headers={"Authorization": f"Bearer {sy_token}"},
        json={
            "transfer_id": transfer_id,
            "gr_number": "123",
            "employee_id": sy_emp.id,
        },
    )
    assert accept.status_code == 200
    assert accept.json()["status"] == "accepted"


def test_reject_and_acknowledge(client, db_session):
    sy_plant, sy_emp = _create_plant(
        db_session, AppRole.SCRAPEYARD, "sy-plant-2"
    )
    sf_plant, sf_emp = _create_plant(
        db_session,
        AppRole.SHOPFLOOR,
        "sf-plant-2",
        linked_id=sy_plant.id,
    )

    sf_token = client.post(
        "/v1/auth/login",
        json={"login_id": "sf-plant-2", "password": "password123"},
    ).json()["access_token"]

    dispatch = client.post(
        "/v1/shopfloor/dispatch",
        headers={"Authorization": f"Bearer {sf_token}"},
        json={
            "qr_raw": SAMPLE_QR.replace("1313", "9999"),
            "gp_number": "126",
            "employee_id": sf_emp.id,
        },
    )
    transfer_id = dispatch.json()["id"]

    sy_token = client.post(
        "/v1/auth/login",
        json={"login_id": "sy-plant-2", "password": "password123"},
    ).json()["access_token"]

    reject = client.post(
        "/v1/scrapeyard/reject",
        headers={"Authorization": f"Bearer {sy_token}"},
        json={
            "transfer_id": transfer_id,
            "reason_type": "quantity_mismatch",
            "qty_received": 90,
            "employee_id": sy_emp.id,
        },
    )
    assert reject.status_code == 200
    assert reject.json()["status"] == "rejected"

    ack = client.post(
        f"/v1/shopfloor/rejected/{transfer_id}/acknowledge",
        headers={
            "Authorization": f"Bearer {sf_token}",
            "X-Employee-Id": str(sf_emp.id),
        },
    )
    assert ack.status_code == 200
    assert ack.json()["status"] == "acknowledged"


def test_admin_plant_crud(client, db_session):
    auth_service.create_admin(db_session, "admin2", "adminpass", "Admin")
    admin_token = client.post(
        "/v1/auth/login",
        json={"login_id": "admin2", "password": "adminpass"},
    ).json()["access_token"]

    create = client.post(
        "/v1/plants",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Unit 3",
            "login_id": "unit3-sf",
            "password": "plantpass",
            "app_role": "shopfloor",
            "employee_names": ["Riya", "Raj"],
        },
    )
    assert create.status_code == 201
    assert len(create.json()["employees"]) == 2

    listing = client.get(
        "/v1/plants",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1
