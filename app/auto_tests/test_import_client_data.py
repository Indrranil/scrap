import os
from decimal import Decimal

import pytest

from app.constants.items import (
    DEFAULT_CLIENT_DATA_XLSX,
    DEFAULT_ITEM_CODE_XLSX,
    PLU_ITEM_CODE_OVERRIDES,
)
from scripts.import_client_data import (
    _load_plu_rows,
    _load_rates_pdf,
    _parse_rate,
    _resolve_item_code,
)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.parametrize(
    "plu,expected_code",
    list(PLU_ITEM_CODE_OVERRIDES.items()),
)
def test_plu_overrides_resolve_to_expected_8digit(plu, expected_code):
    assigned: dict[str, str] = {}
    item_code, shred_out_code, shred_out_name = _resolve_item_code(
        plu, "ANY NAME", {}, assigned
    )
    assert item_code == expected_code
    assert shred_out_code is None
    assert shred_out_name is None
    assert assigned[expected_code] == plu


def test_p_item_has_no_item_code_but_shred_output():
    assigned: dict[str, str] = {}
    item_code, shred_out_code, shred_out_name = _resolve_item_code(
        "P159", "Cartons", {}, assigned
    )
    assert item_code is None
    assert shred_out_code == "1000091259"
    assert shred_out_name == "CARTONS -JT"


def test_parse_rate_handles_invalid_values():
    assert _parse_rate(5.3) == Decimal("5.3")
    assert _parse_rate("13.5") == Decimal("13.5")
    assert _parse_rate("-") is None
    assert _parse_rate("") is None
    assert _parse_rate("N/A") is None
    assert _parse_rate("not-a-number") is None


def test_shared_item_code_allowed_across_plus():
    assigned: dict[str, str] = {}
    code_a, _, _ = _resolve_item_code("1402", "TUBE CUTTING SCRAP", {}, assigned)
    code_b, shred_code, shred_name = _resolve_item_code(
        "P100", "Squeezed Tubes", {}, assigned
    )
    assert code_a == "1000090402"
    assert code_b is None
    assert shred_code == "1000090402"
    assert shred_name == "Empty Tube Scrap"


def test_excel_files_load_without_db_collision():
    item_path = os.path.join(ROOT, DEFAULT_ITEM_CODE_XLSX)
    client_path = os.path.join(ROOT, DEFAULT_CLIENT_DATA_XLSX)
    if not os.path.exists(item_path) or not os.path.exists(client_path):
        pytest.skip("Client Excel files not present in repo")

    plu_rows = _load_plu_rows(item_path)
    rates = _load_rates_pdf(client_path)

    assert len(plu_rows) == 56
    assert len(rates) > 0

    assigned: dict[str, str] = {}
    for plu_code, name, _uom in plu_rows:
        item_code, _, _ = _resolve_item_code(plu_code, name, rates, assigned)
        if item_code and plu_code in PLU_ITEM_CODE_OVERRIDES:
            assert item_code == PLU_ITEM_CODE_OVERRIDES[plu_code]
