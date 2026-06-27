"""PLU codes for KG items that can be shredded at scrapeyard."""

SHREDDABLE_PLU_CODES = frozenset(
    {
        "1499",
        "P159",
        "P106",
        "PB06",
        "PC06",
        "P100",
        "P177",
        "P153",
    }
)

SKIP_VENDOR_ITEM_NAMES = frozenset(
    {
        "IRON DRUM ( UP TO 24 KG )",
        "IRON DRUM ( 25 TO 49 KG )",
    }
)
