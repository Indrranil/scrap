import pytest
from fastapi import HTTPException

from app.services.qr_parser import parse_qr_payload

SAMPLE_QR = """HIDUSTAN UNILEVER LIMITED
DATE: 23-06-2026
TIME: 09:22:02
CODE: 1313
DESCRIPTION: CORRUGATED BOX SCRAP
LOCATION: 3
NET WT.: 7.350 Kg
TARE WT.: 0.000 Kg
GROSS WT.: 7.350 Kg"""

SAMPLE_QR_NO_DESCRIPTION = """HIDUSTAN UNILEVER LIMITED
DATE: 23-06-2026
TIME: 09:22:02
CODE: 1313
LOCATION: 3
NET WT.: 7.350 Kg
GROSS WT.: 7.350 Kg"""


def test_parse_qr_payload():
    payload = parse_qr_payload(SAMPLE_QR)
    assert payload.item_code == "1313"
    assert payload.item_name == "CORRUGATED BOX SCRAP"
    assert payload.plu_code == "1313"
    assert payload.uom == "KG"
    assert float(payload.quantity) == 7.35
    assert payload.location == 3
    assert payload.qr_number


def test_parse_qr_without_description():
    payload = parse_qr_payload(SAMPLE_QR_NO_DESCRIPTION)
    assert payload.item_code == "1313"
    assert payload.item_name is None
    assert payload.uom == "KG"


def test_parse_qr_empty_raises():
    with pytest.raises(HTTPException):
        parse_qr_payload("")
