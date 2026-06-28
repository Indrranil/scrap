#!/usr/bin/env python3
"""Auto-approve GSO-pending transfers older than GSO_AUTO_APPROVE_HOURS."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import SessionLocal
from app.services.transfer import transfer_service


def main() -> None:
    db = SessionLocal()
    try:
        count = transfer_service.auto_approve_expired_gso(db)
        print(f"Auto-approved {count} transfer(s)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
