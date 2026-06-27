import time

from app.auth.jwt_auth import hash_password
from app.models.employee_profile import EmployeeProfile
from app.models.plant import Plant
from app.models.scrapeyard import Scrapeyard

from app.auto_tests.conftest import SAMPLE_QR, SAMPLE_QR_UTE
from app.auto_tests.item_fixtures import seed_ea_item, seed_p_item, seed_test_item


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
    seed_test_item(db_session)
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
            "employee_id": ude_emp.id,
        },
    )
    assert dispatch.status_code == 200
    transfer_id = dispatch.json()["id"]
    assert dispatch.json()["status"] == "dispatched"
    assert dispatch.json()["item_code"] == "1000090313"
    assert dispatch.json()["plu_code"] == "1313"

    sy_token = client.post(
        "/v1/auth/login", json={"login_id": "SCRAP", "password": "1234"}
    ).json()["access_token"]

    accept = client.post(
        "/v1/scrapeyard/accept",
        headers={"Authorization": f"Bearer {sy_token}"},
        json={
            "transfer_id": transfer_id,
            "employee_id": sy_emp.id,
        },
    )
    assert accept.status_code == 200
    assert accept.json()["status"] == "accepted"


def test_dispatch_plant_mismatch_returns_403(client, db_session):
    seed_test_item(
        db_session,
        plu_code="9999",
        item_code="1000090086",
        name="PAPER WASTE",
    )
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
            "employee_id": ude_emp.id,
        },
    )
    assert dispatch.status_code == 403


def test_reject_and_acknowledge(client, db_session):
    seed_test_item(
        db_session,
        plu_code="9999",
        item_code="1000090086",
        name="PAPER WASTE",
    )
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
    seed_test_item(db_session)
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
    assert body["payload"]["item_name"] == "CORRUGATED BOX SCRAP"
    assert body["payload"]["item_code_8"] == "1000090313"


def test_manual_ea_dispatch(client, db_session):
    ea_item = seed_ea_item(db_session)
    _create_scrapeyard(db_session)
    ude, ude_emp = _create_plant(db_session, "UDE", "UDE", 3)

    ude_token = client.post(
        "/v1/auth/login", json={"login_id": "UDE", "password": "1234"}
    ).json()["access_token"]

    items = client.get(
        "/v1/shopfloor/items",
        headers={"Authorization": f"Bearer {ude_token}"},
    )
    assert items.status_code == 200
    assert any(i["id"] == ea_item.id for i in items.json()["items"])

    dispatch = client.post(
        "/v1/shopfloor/dispatch/manual",
        headers={"Authorization": f"Bearer {ude_token}"},
        json={
            "item_master_id": ea_item.id,
            "quantity": "10",
            "material_state": "not_shredded",
            "employee_id": ude_emp.id,
        },
    )
    assert dispatch.status_code == 200
    body = dispatch.json()
    assert body["dispatch_method"] == "manual"
    assert body["uom"] == "EA"
    assert body["quantity_sent"] == "10.000"


def test_ea_qr_dispatch_rejected(client, db_session):
    ea_item = seed_ea_item(db_session)
    _create_scrapeyard(db_session)
    ude, ude_emp = _create_plant(db_session, "UDE", "UDE", 3)

    ea_qr = """HIDUSTAN UNILEVER LIMITED
DATE: 23-06-2026
TIME: 09:22:02
CODE: 1021
LOCATION: 3"""

    ude_token = client.post(
        "/v1/auth/login", json={"login_id": "UDE", "password": "1234"}
    ).json()["access_token"]

    dispatch = client.post(
        "/v1/shopfloor/dispatch",
        headers={"Authorization": f"Bearer {ude_token}"},
        json={"qr_raw": ea_qr, "employee_id": ude_emp.id},
    )
    assert dispatch.status_code == 422
    assert "manual dispatch" in dispatch.json()["detail"].lower()


def test_shreddable_item_requires_material_state(client, db_session):
    seed_p_item(
        db_session,
        plu_code="P106",
        name="Bottles & Caps",
        shred_output_item_code="1000090406",
        shred_output_name="LIQUID MIX BOTTLE & CAPS SCRAP",
    )
    _create_scrapeyard(db_session)
    ude, ude_emp = _create_plant(db_session, "UDE", "UDE", 3)

    shreddable_qr = """HIDUSTAN UNILEVER LIMITED
DATE: 23-06-2026
TIME: 09:22:02
CODE: P106
LOCATION: 3
NET WT.: 5.000 Kg
GROSS WT.: 5.000 Kg"""

    ude_token = client.post(
        "/v1/auth/login", json={"login_id": "UDE", "password": "1234"}
    ).json()["access_token"]

    missing_state = client.post(
        "/v1/shopfloor/dispatch",
        headers={"Authorization": f"Bearer {ude_token}"},
        json={"qr_raw": shreddable_qr, "employee_id": ude_emp.id},
    )
    assert missing_state.status_code == 422

    dispatch = client.post(
        "/v1/shopfloor/dispatch",
        headers={"Authorization": f"Bearer {ude_token}"},
        json={
            "qr_raw": shreddable_qr,
            "employee_id": ude_emp.id,
            "material_state": "shredded",
        },
    )
    assert dispatch.status_code == 200
    assert dispatch.json()["material_state"] == "shredded"
    assert dispatch.json()["is_shreddable"] is True
    assert dispatch.json()["is_p_item"] is True
    assert dispatch.json()["item_code"] == "P106"
    assert dispatch.json()["item_name"] == "Bottles & Caps"


def test_p_item_dispatch_hides_8digit_until_shred(client, db_session):
    seed_p_item(db_session)
    sy, sy_emp = _create_scrapeyard(db_session)
    ude, ude_emp = _create_plant(db_session, "UDE", "UDE", 3)

    p_qr = """HIDUSTAN UNILEVER LIMITED
DATE: 23-06-2026
TIME: 09:22:02
CODE: P159
LOCATION: 3
NET WT.: 12.000 Kg
GROSS WT.: 12.000 Kg"""

    ude_token = client.post(
        "/v1/auth/login", json={"login_id": "UDE", "password": "1234"}
    ).json()["access_token"]

    scan = client.post(
        "/v1/transfers/scan",
        headers={"Authorization": f"Bearer {ude_token}"},
        json={"qr_raw": p_qr},
    )
    assert scan.status_code == 200
    payload = scan.json()["payload"]
    assert payload["item_name"] == "Cartons"
    assert payload["is_p_item"] is True
    assert payload["item_code_8"] is None

    dispatch = client.post(
        "/v1/shopfloor/dispatch",
        headers={"Authorization": f"Bearer {ude_token}"},
        json={
            "qr_raw": p_qr,
            "employee_id": ude_emp.id,
            "material_state": "not_shredded",
        },
    )
    assert dispatch.status_code == 200
    body = dispatch.json()
    assert body["item_code"] == "P159"
    assert body["item_name"] == "Cartons"
    assert body["is_p_item"] is True
    transfer_id = body["id"]

    sy_token = client.post(
        "/v1/auth/login", json={"login_id": "SCRAP", "password": "1234"}
    ).json()["access_token"]

    accept = client.post(
        "/v1/scrapeyard/accept",
        headers={"Authorization": f"Bearer {sy_token}"},
        json={"transfer_id": transfer_id, "employee_id": sy_emp.id},
    )
    assert accept.status_code == 200
    assert accept.json()["item_name"] == "Cartons"
    assert accept.json()["item_code"] == "P159"

    shred = client.post(
        "/v1/scrapeyard/shred",
        headers={"Authorization": f"Bearer {sy_token}"},
        json={
            "transfer_id": transfer_id,
            "quantity_kg": "12.000",
            "employee_id": sy_emp.id,
        },
    )
    assert shred.status_code == 201
    log = shred.json()
    assert log["input_plu_code"] == "P159"
    assert log["input_name"] == "Cartons"
    assert log["output_item_code"] == "1000091259"
    assert log["output_name"] == "CARTONS -JT"
    assert log["quantity_kg"] == "12.000"

    logs = client.get(
        "/v1/scrapeyard/shred-log",
        headers={"Authorization": f"Bearer {sy_token}"},
    )
    assert logs.status_code == 200
    assert logs.json()["total"] == 1
    assert logs.json()["items"][0]["id"] == log["id"]

    detail = client.get(
        f"/v1/scrapeyard/shred-log/{log['id']}",
        headers={"Authorization": f"Bearer {sy_token}"},
    )
    assert detail.status_code == 200
    assert detail.json()["output_item_code"] == "1000091259"


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
