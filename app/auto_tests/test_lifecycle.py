import time

from app.auth.jwt_auth import hash_password
from app.models.employee_profile import EmployeeProfile
from app.models.plant import Plant
from app.models.scrapeyard import Scrapeyard

from app.auto_tests.conftest import SAMPLE_QR, SAMPLE_QR_UTE


def _create_scrapeyard(db):
    sy = Scrapeyard(
        name="Central Scrapeyard",
        login_id="SCRAP",
        password_hash=hash_password("1234"),
        is_active=True,
        created_at=int(time.time()),
    )
    db.add(sy)
    db.flush()
    emp = EmployeeProfile(
        scrapeyard_id=sy.id,
        name="SY Employee",
        is_active=True,
        created_at=int(time.time()),
    )
    db.add(emp)
    db.commit()
    db.refresh(sy)
    db.refresh(emp)
    return sy, emp


def _create_plant(db, code, login_id, qr_location):
    plant = Plant(
        code=code,
        name=code,
        login_id=login_id,
        password_hash=hash_password("1234"),
        qr_location=qr_location,
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
    sy, sy_emp = _create_scrapeyard(db_session)
    ude, ude_emp = _create_plant(db_session, "UDE", "UDE", 3)

    ude_token = client.post(
        "/v1/auth/login", json={"login_id": "UDE", "password": "1234"}
    ).json()["access_token"]

    dispatch = client.post(
        "/v1/shopfloor/dispatch",
        headers={"Authorization": f"Bearer {ude_token}"},
        json={
            "qr_raw": SAMPLE_QR,
            "gp_number": "125",
            "employee_id": ude_emp.id,
        },
    )
    assert dispatch.status_code == 200
    transfer_id = dispatch.json()["id"]
    assert dispatch.json()["status"] == "dispatched"

    sy_token = client.post(
        "/v1/auth/login", json={"login_id": "SCRAP", "password": "1234"}
    ).json()["access_token"]

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


def test_dispatch_plant_mismatch_returns_403(client, db_session):
    _create_scrapeyard(db_session)
    ude, ude_emp = _create_plant(db_session, "UDE", "UDE", 3)
    _create_plant(db_session, "UTE", "UTE", 2)

    ude_token = client.post(
        "/v1/auth/login", json={"login_id": "UDE", "password": "1234"}
    ).json()["access_token"]

    dispatch = client.post(
        "/v1/shopfloor/dispatch",
        headers={"Authorization": f"Bearer {ude_token}"},
        json={
            "qr_raw": SAMPLE_QR_UTE,
            "gp_number": "126",
            "employee_id": ude_emp.id,
        },
    )
    assert dispatch.status_code == 403


def test_reject_and_acknowledge(client, db_session):
    sy, sy_emp = _create_scrapeyard(db_session)
    ute, ute_emp = _create_plant(db_session, "UTE", "UTE", 2)

    ute_token = client.post(
        "/v1/auth/login", json={"login_id": "UTE", "password": "1234"}
    ).json()["access_token"]

    dispatch = client.post(
        "/v1/shopfloor/dispatch",
        headers={"Authorization": f"Bearer {ute_token}"},
        json={
            "qr_raw": SAMPLE_QR_UTE,
            "gp_number": "126",
            "employee_id": ute_emp.id,
        },
    )
    assert dispatch.status_code == 200
    transfer_id = dispatch.json()["id"]

    sy_token = client.post(
        "/v1/auth/login", json={"login_id": "SCRAP", "password": "1234"}
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
            "Authorization": f"Bearer {ute_token}",
            "X-Employee-Id": str(ute_emp.id),
        },
    )
    assert ack.status_code == 200
    assert ack.json()["status"] == "acknowledged"


def test_scan_returns_plant_match(client, db_session):
    _create_plant(db_session, "UDE", "UDE", 3)

    ude_token = client.post(
        "/v1/auth/login", json={"login_id": "UDE", "password": "1234"}
    ).json()["access_token"]

    scan = client.post(
        "/v1/transfers/scan",
        headers={"Authorization": f"Bearer {ude_token}"},
        json={"qr_raw": SAMPLE_QR},
    )
    assert scan.status_code == 200
    body = scan.json()
    assert body["resolved_plant"]["login_id"] == "UDE"
    assert body["plant_match"] is True


def test_admin_plant_crud(client, db_session):
    from app.services.auth import auth_service

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
            "qr_location": 99,
            "employee_names": ["Riya", "Raj"],
        },
    )
    assert create.status_code == 201
    assert len(create.json()["employees"]) == 2
