"""Item master constants for import and dispatch."""

PLU_ITEM_CODE_OVERRIDES: dict[str, str] = {
    "1402": "1000091253",
    "1081": "1000524070",
    "1430": "1000524071",
    "1763": "1000090763",
    "1313": "1000090313",
    "1259": "1000091259",
    "1750": "1000090766",
    "1253": "1000091253",
    "1314": "1000090314",
    "1021": "1000090021",
}

P_ITEM_SHRED_OUTPUTS: dict[str, tuple[str, str]] = {
    "P159": ("1000091259", "CARTONS -JT"),
    "P106": ("1000090406", "LIQUID MIX BOTTLE & CAPS SCRAP"),
    "PB06": ("1000090406", "LIQUID MIX BOTTLE & CAPS SCRAP"),
    "PC06": ("1000090406", "LIQUID MIX BOTTLE & CAPS SCRAP"),
    "P153": ("1000091253", "TUBE CUTTING-JT"),
    "P100": ("1000090402", "Empty Tube Scrap"),
    "P177": ("1000090077", "SHREDED LAMINATES"),
}

SHREDDABLE_PLU_CODES = frozenset(P_ITEM_SHRED_OUTPUTS.keys())

SKIP_VENDOR_ITEM_NAMES = frozenset(
    {
        "IRON DRUM ( UP TO 24 KG )",
        "IRON DRUM ( 25 TO 49 KG )",
    }
)

DEFAULT_ITEM_CODE_XLSX = "upated_itemcode.xlsx"
DEFAULT_CLIENT_DATA_XLSX = "updated_8digit.xlsx"
