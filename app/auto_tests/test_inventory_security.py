import time

from app.auth.jwt_auth import hash_password
from app.models.employee_profile import EmployeeProfile

from app.auto_tests.conftest import SAMPLE_QR
from app.auto_tests.item_fixtures import seed_test_item
from app.auto_tests.test_lifecycle import (
    _create_gso,
    _create_plant,
    _create_scrapeyard,
    _gso_approve,
)


def _create_security(db):
    from app.models.security import Security

    sec = Security(
        name="Security Gate",
        login_id="Security-1",
        password_hash=hash_password("1234"),
        is_active=True,
        created_at=int(time.time()),
    )
    db.add(sec)
    db.flush()
    emp = EmployeeProfile(
        security_id=sec.id,
        name="Security Employee",
        is_active=True,
        created_at=int(time.time()),
    )
    db.add(emp)
    db.commit()
    db.refresh(sec)
    db.refresh(emp)
    return sec, emp


def test_accept_non_p_adds_inventory(client, db_session):
    from app.models.material_inventory import MaterialInventory

    seed_test_item(db_session)
    sy, sy_emp = _create_scrapeyard(db_session)
    ude, ude_emp = _create_plant(db_session, "UDE", "UDE", 3)
    _, gso_emp = _create_gso(db_session, ude)

    ude_token = client.post(
        "/v1/auth/login", json={"login_id": "UDE", "password": "1234"}
    ).json()["access_token"]
    dispatch = client.post(
        "/v1/shopfloor/dispatch",
        headers={"Authorization": f"Bearer {ude_token}"},
        json={"qr_raw": SAMPLE_QR, "employee_id": ude_emp.id},
    )
    transfer_id = dispatch.json()["id"]
    _gso_approve(client, gso_emp, transfer_id)

    sy_token = client.post(
        "/v1/auth/login", json={"login_id": "SCRAP", "password": "1234"}
    ).json()["access_token"]
    client.post(
        "/v1/scrapeyard/accept",
        headers={"Authorization": f"Bearer {sy_token}"},
        json={"transfer_id": transfer_id, "employee_id": sy_emp.id},
    )

    inv = (
        db_session.query(MaterialInventory)
        .filter(MaterialInventory.item_code == "1000090313")
        .first()
    )
    assert inv is not None
    assert float(inv.quantity_available) == 7.35

    ready = client.get(
        "/v1/scrapeyard/ready-for-sale",
        headers={"Authorization": f"Bearer {sy_token}"},
    )
    assert ready.status_code == 200
    assert ready.json()["total"] == 1


def test_security_sale_deducts_inventory(client, db_session):
    from app.models.material_inventory import MaterialInventory
    from app.models.vendor import Vendor

    seed_test_item(db_session)
    sy, sy_emp = _create_scrapeyard(db_session)
    ude, ude_emp = _create_plant(db_session, "UDE", "UDE", 3)
    _, gso_emp = _create_gso(db_session, ude)
    _, sec_emp = _create_security(db_session)

    vendor = Vendor(name="Radheman Enterprises", is_active=True, created_at=int(time.time()))
    db_session.add(vendor)
    db_session.commit()

    ude_token = client.post(
        "/v1/auth/login", json={"login_id": "UDE", "password": "1234"}
    ).json()["access_token"]
    dispatch = client.post(
        "/v1/shopfloor/dispatch",
        headers={"Authorization": f"Bearer {ude_token}"},
        json={"qr_raw": SAMPLE_QR, "employee_id": ude_emp.id},
    )
    transfer_id = dispatch.json()["id"]
    _gso_approve(client, gso_emp, transfer_id)

    sy_token = client.post(
        "/v1/auth/login", json={"login_id": "SCRAP", "password": "1234"}
    ).json()["access_token"]
    client.post(
        "/v1/scrapeyard/accept",
        headers={"Authorization": f"Bearer {sy_token}"},
        json={"transfer_id": transfer_id, "employee_id": sy_emp.id},
    )

    sec_token = client.post(
        "/v1/auth/login", json={"login_id": "Security-1", "password": "1234"}
    ).json()["access_token"]

    sale = client.post(
        "/v1/security/sales",
        headers={"Authorization": f"Bearer {sec_token}"},
        json={
            "item_code": "1000090313",
            "vendor_id": vendor.id,
            "vehicle_number": "HR32EA1212",
            "quantity_sold": "5.000",
            "employee_id": sec_emp.id,
        },
    )
    assert sale.status_code == 201
    assert sale.json()["status"] == "pending"
    assert sale.json()["display_status"] == "Material Sale"

    inv = (
        db_session.query(MaterialInventory)
        .filter(MaterialInventory.item_code == "1000090313")
        .first()
    )
    assert float(inv.quantity_available) == 2.35


def test_security_sale_exceeds_available_returns_422(client, db_session):
    from app.models.vendor import Vendor

    seed_test_item(db_session)
    sy, sy_emp = _create_scrapeyard(db_session)
    ude, ude_emp = _create_plant(db_session, "UDE", "UDE", 3)
    _, gso_emp = _create_gso(db_session, ude)
    _, sec_emp = _create_security(db_session)

    vendor = Vendor(name="Vendor A", is_active=True, created_at=int(time.time()))
    db_session.add(vendor)
    db_session.commit()

    ude_token = client.post(
        "/v1/auth/login", json={"login_id": "UDE", "password": "1234"}
    ).json()["access_token"]
    dispatch = client.post(
        "/v1/shopfloor/dispatch",
        headers={"Authorization": f"Bearer {ude_token}"},
        json={"qr_raw": SAMPLE_QR, "employee_id": ude_emp.id},
    )
    transfer_id = dispatch.json()["id"]
    _gso_approve(client, gso_emp, transfer_id)

    sy_token = client.post(
        "/v1/auth/login", json={"login_id": "SCRAP", "password": "1234"}
    ).json()["access_token"]
    client.post(
        "/v1/scrapeyard/accept",
        headers={"Authorization": f"Bearer {sy_token}"},
        json={"transfer_id": transfer_id, "employee_id": sy_emp.id},
    )

    sec_token = client.post(
        "/v1/auth/login", json={"login_id": "Security-1", "password": "1234"}
    ).json()["access_token"]

    sale = client.post(
        "/v1/security/sales",
        headers={"Authorization": f"Bearer {sec_token}"},
        json={
            "item_code": "1000090313",
            "vendor_id": vendor.id,
            "vehicle_number": "HR32EA1212",
            "quantity_sold": "999.000",
            "employee_id": sec_emp.id,
        },
    )
    assert sale.status_code == 422
