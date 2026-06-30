import time

from app.auth.jwt_auth import hash_password
from app.models.employee_profile import EmployeeProfile
from app.models.material_inventory import MaterialInventory
from app.models.scrapeyard import Scrapeyard
from app.models.security import Security
from app.models.vendor import Vendor
from app.services.auth import auth_service

from app.auto_tests.item_fixtures import seed_test_item
from app.auto_tests.test_lifecycle import _create_plant


def _admin_token(client, db_session):
    auth_service.create_admin(db_session, "admin", "Admin@123", "System Admin")
    return client.post(
        "/v1/auth/login", json={"login_id": "admin", "password": "Admin@123"}
    ).json()["access_token"]


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
    db.add(
        EmployeeProfile(
            scrapeyard_id=sy.id,
            name="SY Worker",
            is_active=True,
            created_at=int(time.time()),
        )
    )
    db.commit()
    db.refresh(sy)
    return sy


def _create_security(db):
    sec = Security(
        name="Security Gate",
        login_id="Security-1",
        password_hash=hash_password("1234"),
        is_active=True,
        created_at=int(time.time()),
    )
    db.add(sec)
    db.flush()
    db.add(
        EmployeeProfile(
            security_id=sec.id,
            name="Sec Employee",
            is_active=True,
            created_at=int(time.time()),
        )
    )
    db.commit()
    db.refresh(sec)
    return sec


def test_plant_create_auto_provisions_gso(client, db_session):
    token = _admin_token(client, db_session)
    resp = client.post(
        "/v1/plants",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "code": "UDE",
            "name": "Unit 3",
            "login_id": "UDE",
            "password": "securepass",
            "qr_location": 3,
            "employee_names": ["Alice"],
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["generated_password"] == "securepass"
    plant_id = body["id"]

    gso = client.get(
        f"/v1/plants/{plant_id}/gso",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert gso.status_code == 200
    assert gso.json()["login_id"] == "GSO-UDE"
    assert gso.json()["plant_id"] == plant_id


def test_plant_credentials_endpoint(client, db_session):
    token = _admin_token(client, db_session)
    plant, _ = _create_plant(db_session, "UTE", "UTE", 2)
    resp = client.get(
        f"/v1/plants/{plant.id}/credentials",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"login_id": "UTE", "has_password": True}


def test_security_config(client, db_session):
    token = _admin_token(client, db_session)
    _create_security(db_session)

    get_resp = client.get(
        "/v1/security-config",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["login_id"] == "Security-1"

    patch_resp = client.patch(
        "/v1/security-config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "employee_names": ["Worker A", "Worker B"],
            "password": "newsec123",
        },
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["generated_password"] == "newsec123"
    assert len(patch_resp.json()["employees"]) == 2


def test_gso_config_update(client, db_session):
    token = _admin_token(client, db_session)
    plant, _ = _create_plant(db_session, "U535", "Unit 4", 4)
    from app.services.gso_admin import gso_admin_service

    gso_admin_service.ensure_gso_for_plant(db_session, plant)
    db_session.commit()

    resp = client.patch(
        f"/v1/plants/{plant.id}/gso",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "login_id": "GSO-U535",
            "employee_names": ["GSO One"],
            "password": "gso1234",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["generated_password"] == "gso1234"
    assert resp.json()["employees"][0]["name"] == "GSO One"


def test_admin_profile(client, db_session):
    token = _admin_token(client, db_session)

    get_resp = client.get(
        "/v1/admin/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["username"] == "admin"

    patch_resp = client.patch(
        "/v1/admin/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Updated Admin",
            "old_password": "Admin@123",
            "new_password": "NewAdmin@456",
        },
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Updated Admin"

    login = client.post(
        "/v1/auth/login", json={"login_id": "admin", "password": "NewAdmin@456"}
    )
    assert login.status_code == 200


def test_material_sale_approve_reject(client, db_session):
    from app.auto_tests.test_inventory_security import _create_security

    seed_test_item(db_session)
    _create_scrapeyard(db_session)
    sec, sec_emp = _create_security(db_session)
    admin_token = _admin_token(client, db_session)

    db_session.add(
        MaterialInventory(
            scrapeyard_id=1,
            item_code="1000090313",
            item_name="CORRUGATED BOX SCRAP",
            uom="KG",
            quantity_available=100,
            updated_at=int(time.time()),
        )
    )
    vendor = Vendor(name="Test Vendor", is_active=True, created_at=int(time.time()))
    db_session.add(vendor)
    db_session.commit()
    db_session.refresh(vendor)

    sec_token = client.post(
        "/v1/auth/login", json={"login_id": "Security-1", "password": "1234"}
    ).json()["access_token"]
    sale_resp = client.post(
        "/v1/security/sales",
        headers={"Authorization": f"Bearer {sec_token}"},
        json={
            "item_code": "1000090313",
            "vendor_id": vendor.id,
            "vehicle_number": "HR301212",
            "quantity_sold": "10",
            "employee_id": sec_emp.id,
        },
    )
    assert sale_resp.status_code == 201
    sale_id = sale_resp.json()["id"]

    pending = client.get(
        "/v1/material-sales",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pending.status_code == 200
    assert pending.json()["total"] == 1

    reject_resp = client.post(
        f"/v1/material-sales/{sale_id}/reject",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"reason": "Incorrect quantity"},
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"

    inv = (
        db_session.query(MaterialInventory)
        .filter(MaterialInventory.item_code == "1000090313")
        .first()
    )
    assert float(inv.quantity_available) == 100

    sale_resp2 = client.post(
        "/v1/security/sales",
        headers={"Authorization": f"Bearer {sec_token}"},
        json={
            "item_code": "1000090313",
            "vendor_id": vendor.id,
            "vehicle_number": "HR301213",
            "quantity_sold": "5",
            "employee_id": sec_emp.id,
        },
    )
    sale_id2 = sale_resp2.json()["id"]
    approve_resp = client.post(
        f"/v1/material-sales/{sale_id2}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"


def test_items_with_vendors_and_filters(client, db_session):
    token = _admin_token(client, db_session)
    vendor = Vendor(
        name="Vendor A",
        vendor_code="V001",
        is_active=True,
        created_at=int(time.time()),
    )
    db_session.add(vendor)
    db_session.commit()
    db_session.refresh(vendor)

    create_resp = client.post(
        "/v1/items/with-vendors",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "plu_code": "1414",
            "item_code": "1000090414",
            "name": "TEST SCRAP",
            "uom": "KG",
            "is_shreddable": False,
            "is_p_item": False,
            "vendors": [{"vendor_id": vendor.id, "rate_inr": "12.50"}],
        },
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["vendors"][0]["rate_inr"] == "12.50"

    list_resp = client.get(
        "/v1/items?is_p_item=false",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    assert list_resp.json()["items"][0]["rate_inr"] == "12.50"

    options = client.get(
        "/v1/items/post-shred-options",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert options.status_code == 200
    assert options.json()["total"] >= 1


def test_vendor_create_with_items_and_code_filter(client, db_session):
    token = _admin_token(client, db_session)
    seed_test_item(db_session)
    from app.models.item_master import ItemMaster

    item = db_session.query(ItemMaster).first()

    create_resp = client.post(
        "/v1/vendors",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Seven Star",
            "vendor_code": "10245",
            "gst_number": "GST123",
            "items": [{"item_id": item.id, "rate_inr": "8.00"}],
        },
    )
    assert create_resp.status_code == 201

    list_resp = client.get(
        "/v1/vendors?vendor_code=10245",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1
    assert list_resp.json()["items"][0]["vendor_code"] == "10245"
