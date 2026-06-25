import hashlib
import re
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional

from fastapi import HTTPException

from app.schemas.transfer import QRPayload

_KEY_PATTERN = re.compile(r"^([A-Z][A-Z0-9 .]*?)\s*:\s*(.+)$", re.MULTILINE)


def _parse_key_value_lines(qr_raw: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for line in qr_raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        match = _KEY_PATTERN.match(line)
        if match:
            key = match.group(1).strip().upper()
            value = match.group(2).strip()
            data[key] = value
    return data


def _parse_weight(value: str) -> Optional[Decimal]:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9.]", "", value.replace(",", ""))
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _normalize_key(key: str) -> str:
    return re.sub(r"\s+", " ", key.strip().upper())


def parse_qr_payload(qr_raw: str) -> QRPayload:
    if not qr_raw or not qr_raw.strip():
        raise HTTPException(status_code=422, detail="QR payload is empty")

    data = _parse_key_value_lines(qr_raw)
    if not data:
        raise HTTPException(status_code=422, detail="Unable to parse QR payload")

    normalized = {_normalize_key(k): v for k, v in data.items()}

    item_code = normalized.get("CODE")
    description = normalized.get("DESCRIPTION")
    if not item_code or not description:
        raise HTTPException(
            status_code=422,
            detail="QR payload must include CODE and DESCRIPTION",
        )

    net_weight = _parse_weight(normalized.get("NET WT.", normalized.get("NET WT", "")))
    tare_weight = _parse_weight(
        normalized.get("TARE WT.", normalized.get("TARE WT", ""))
    )
    gross_weight = _parse_weight(
        normalized.get("GROSS WT.", normalized.get("GROSS WT", ""))
    )

    location_val = normalized.get("LOCATION")
    location = int(location_val) if location_val and location_val.isdigit() else None

    if gross_weight is not None and gross_weight > 0:
        uom = "KG"
        quantity = gross_weight
    elif net_weight is not None and net_weight > 0:
        uom = "KG"
        quantity = net_weight
    else:
        uom = "EA"
        quantity = Decimal("1")

    date_str = normalized.get("DATE")
    time_str = normalized.get("TIME")

    qr_number = hashlib.sha256(qr_raw.encode()).hexdigest()[:16]

    return QRPayload(
        qr_number=qr_number,
        item_code=item_code,
        item_name=description,
        description=description,
        location=location,
        net_weight=net_weight,
        tare_weight=tare_weight,
        gross_weight=gross_weight,
        uom=uom,
        quantity=quantity,
        date_str=date_str,
        time_str=time_str,
    )
