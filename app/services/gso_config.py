from os import getenv


def gso_approval_enabled() -> bool:
    return getenv("GSO_APPROVAL_ENABLED", "true").lower() in ("1", "true", "yes")


def gso_auto_approve_seconds() -> int:
    return int(getenv("GSO_AUTO_APPROVE_HOURS", "2")) * 3600
