# DigiScrapyard API — Frontend Integration Guide

Base URL: `http://<host>:<port>` (default `http://localhost:8000`)

Interactive docs: `/docs` (Swagger) · `/redoc`

---

## Authentication

### Login

`POST /v1/auth/login` (public)

**Plant login (Shopfloor / Scrapeyard):**
```json
{
  "login_id": "unit3-sf",
  "password": "plantpass",
  "app_role": "shopfloor"
}
```

`app_role` is optional but recommended when the same login_id could exist for both roles.

**Admin login:**
```json
{
  "login_id": "admin",
  "password": "Admin@123"
}
```

**Response:**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "role": "shopfloor",
  "plant_id": 1,
  "plant_name": "Unit 3",
  "employees": [{ "id": 1, "name": "Rohan" }]
}
```

### Authenticated requests

```
Authorization: Bearer <access_token>
```

For mutating shopfloor/scrapeyard actions, also send:
```
X-Employee-Id: <employee_profile_id>
```
(or pass `employee_id` in the JSON body where documented)

### Logout

`POST /v1/auth/logout` — client discards token locally.

---

## Role → Endpoint Matrix

| Endpoint | Shopfloor | Scrapeyard | Admin |
|----------|-----------|------------|-------|
| `POST /v1/auth/login` | ✓ | ✓ | ✓ |
| `GET /v1/employees` | ✓ | ✓ | |
| `POST /v1/transfers/scan` | ✓ | ✓ | |
| `GET /v1/transfers/history` | ✓ | ✓ | ✓ |
| `GET /v1/transfers/{id}` | ✓ | ✓ | ✓ |
| `POST /v1/shopfloor/dispatch` | ✓ | | |
| `GET /v1/shopfloor/rejected` | ✓ | | |
| `POST /v1/shopfloor/rejected/{id}/acknowledge` | ✓ | | |
| `POST /v1/scrapeyard/accept` | | ✓ | |
| `POST /v1/scrapeyard/reject` | | ✓ | |
| `GET/POST/PATCH/DELETE /v1/plants` | | | ✓ |
| `GET /v1/reporting/*` | | | ✓ |
| `GET/POST /v1/sales` | | | ✓ |
| `POST /v1/images/upload` | ✓ | ✓ | ✓ |

---

## Transfer Flow

```mermaid
sequenceDiagram
    participant SF as Shopfloor App
    participant API as API
    participant SY as Scrapeyard App

    SF->>API: POST /v1/transfers/scan
    API-->>SF: Material preview
    SF->>API: POST /v1/shopfloor/dispatch
    API-->>SF: status=dispatched
    SY->>API: POST /v1/transfers/scan
    API-->>SY: Existing transfer info
    alt Accept
        SY->>API: POST /v1/scrapeyard/accept
        API-->>SY: status=accepted
    else Reject
        SY->>API: POST /v1/scrapeyard/reject
        API-->>SY: status=rejected
        SF->>API: POST /v1/shopfloor/rejected/{id}/acknowledge
        API-->>SF: status=acknowledged
    end
```

### 1. Scan QR

`POST /v1/transfers/scan`
```json
{ "qr_raw": "DATE: 23-06-2026\nCODE: 1313\nDESCRIPTION: CORRUGATED BOX SCRAP\nGROSS WT.: 7.350 Kg" }
```

**Response:**
```json
{
  "payload": {
    "qr_number": "a1b2c3...",
    "item_code": "1313",
    "item_name": "CORRUGATED BOX SCRAP",
    "uom": "KG",
    "quantity": "7.350",
    "gross_weight": "7.350"
  },
  "existing_transfer_id": null,
  "existing_status": null
}
```

### 2. Dispatch (Shopfloor)

`POST /v1/shopfloor/dispatch`
```json
{
  "qr_raw": "<same scanned string>",
  "gp_number": "125",
  "employee_id": 1,
  "photo_path": "transfers/photo.jpg"
}
```

### 3. Accept (Scrapeyard)

`POST /v1/scrapeyard/accept`
```json
{
  "transfer_id": 1,
  "gr_number": "123",
  "employee_id": 2,
  "photo_path": "transfers/accept.jpg"
}
```

### 4. Reject (Scrapeyard)

`POST /v1/scrapeyard/reject`

**Quantity mismatch:**
```json
{
  "transfer_id": 1,
  "reason_type": "quantity_mismatch",
  "qty_received": 90,
  "employee_id": 2
}
```

**Wrong material:**
```json
{
  "transfer_id": 1,
  "reason_type": "wrong_material",
  "material_received_name": "Plastic Bottles",
  "employee_id": 2
}
```

**Others:**
```json
{
  "transfer_id": 1,
  "reason_type": "others",
  "comment": "Wrong QR",
  "employee_id": 2
}
```

### 5. Acknowledge rejection (Shopfloor)

`POST /v1/shopfloor/rejected/{transfer_id}/acknowledge`

Headers: `X-Employee-Id: 1`

---

## History & Filters

`GET /v1/transfers/history?page=1&page_size=50&status=accepted&date_from=2026-01-01&date_to=2026-06-30&item_code=1313&material_name=SCRAP`

`GET /v1/shopfloor/rejected` — rejected items awaiting acknowledgement

`GET /v1/transfers/{id}` — detail with timeline events and rejection info

**Transfer detail response fields:** `qr_number`, `item_code`, `item_name`, `gp_number`, `gr_number`, `uom`, `quantity_sent`, `quantity_received`, `status`, `events[]`, `rejection`

---

## Admin — Plant Management

### List plants

`GET /v1/plants?search=UDE`

### Create plant

`POST /v1/plants`
```json
{
  "code": "UDE",
  "name": "Unit 3",
  "login_id": "unit3-sf",
  "password": "securepass",
  "app_role": "shopfloor",
  "address": "Doom Dooma, Assam",
  "linked_scrapeyard_plant_id": 2,
  "employee_names": ["Riya", "Rishabh", "Raj"]
}
```

### Update / Delete / Copy

- `PATCH /v1/plants/{id}`
- `DELETE /v1/plants/{id}` (soft deactivate)
- `POST /v1/plants/{id}/copy`

---

## Admin — Reporting

All reporting endpoints accept `plant_id`, `date_from`, `date_to` (YYYY-MM-DD).

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/reporting/summary` | KPI cards |
| `GET /v1/reporting/plant-generation` | Bar chart by plant |
| `GET /v1/reporting/rejection-reasons` | Donut chart |
| `GET /v1/reporting/accepted-vs-sold` | Bar chart |
| `GET /v1/reporting/recent-transfers` | Recent table |

### Record sale

`POST /v1/sales`
```json
{
  "transfer_id": 1,
  "plant_id": 2,
  "quantity_kg": 7.35,
  "quantity_ea": 0,
  "amount_inr": 84000.00,
  "notes": "Sold after shredding"
}
```

---

## Images

`POST /v1/images/upload` — multipart file upload; returns `{ "path": "..." }`

Use returned `path` as `photo_path` in dispatch/accept/reject requests.

`GET /v1/images/?path=<relative_path>` — serve image

---

## Error Codes

| Code | Meaning |
|------|---------|
| 401 | Missing/invalid token |
| 403 | Wrong role or plant |
| 404 | Resource not found |
| 409 | Duplicate QR / login ID |
| 422 | Validation error (missing rejection fields, bad QR) |

---

## Pagination

List endpoints use `page` (1-based) and `page_size` (max 200).

Response shape: `{ "total": N, "items": [...] }`

---

## Status Values

`pending` → `dispatched` → `accepted` | `rejected` → `acknowledged` | `sold`
