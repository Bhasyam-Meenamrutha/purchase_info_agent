
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "purchase_info.db"


def get_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def initialize_database():
    """Create the table and uniqueness constraint if needed."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS purchase_info_records (
                info_record_number TEXT PRIMARY KEY,
                supplier TEXT NOT NULL,
                material TEXT NOT NULL,
                purchasing_organization TEXT NOT NULL,
                plant TEXT NOT NULL DEFAULT '',
                net_price REAL NOT NULL CHECK (net_price > 0),
                currency TEXT NOT NULL,
                order_unit TEXT NOT NULL,
                planned_delivery_time INTEGER NOT NULL
                    CHECK (planned_delivery_time >= 0),
                info_record_category TEXT NOT NULL,
                created_at TEXT NOT NULL,
                record_json TEXT NOT NULL,

                UNIQUE (
                    supplier,
                    material,
                    purchasing_organization,
                    info_record_category
                )
            )
        """)


def _business_key(record):
    return (
        record["supplier"],
        record["material"],
        record["purchasing_organization"],
        record["info_record_category"],
    )


def _row_to_record(row):
    if row is None:
        return None

    return json.loads(row["record_json"])


def find_purchase_info_record(
    supplier: str,
    material: str,
    purchasing_organization: str,
    info_record_category: str = "STANDARD",
):
    """Find a record by the dummy business key."""

    with get_connection() as conn:
        row = conn.execute("""
            SELECT record_json
            FROM purchase_info_records
            WHERE supplier = ?
              AND material = ?
              AND purchasing_organization = ?
              AND info_record_category = ?
        """, (
            supplier.strip(),
            material.strip(),
            purchasing_organization.strip(),
            info_record_category.strip().upper(),
        )).fetchone()

    return _row_to_record(row)


def create_dummy_purchase_info_record(data: dict):
    """Create and persist a simulated Purchase Info Record."""

    initialize_database()

    import uuid

    record_id = f"DUMMY-{uuid.uuid4().hex[:8].upper()}"

    record = {
        "info_record_number": record_id,
        **data,
        "status": "CREATED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "system": "DUMMY_SAP",
    }

    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO purchase_info_records (
                    info_record_number,
                    supplier,
                    material,
                    purchasing_organization,
                    plant,
                    net_price,
                    currency,
                    order_unit,
                    planned_delivery_time,
                    info_record_category,
                    created_at,
                    record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["info_record_number"],
                record["supplier"],
                record["material"],
                record["purchasing_organization"],
                record.get("plant", ""),
                record["net_price"],
                record["currency"],
                record["order_unit"],
                record["planned_delivery_time"],
                record["info_record_category"],
                record["created_at"],
                json.dumps(record),
            ))

    except sqlite3.IntegrityError:
        existing = find_purchase_info_record(
            supplier=data["supplier"],
            material=data["material"],
            purchasing_organization=data["purchasing_organization"],
            info_record_category=data["info_record_category"],
        )

        return {
            "success": False,
            "message": "A matching Purchase Info Record already exists.",
            "existing_record": existing,
            "system": "DUMMY_SAP",
        }

    return {
        "success": True,
        "message": "Purchase Info Record created successfully.",
        "record": record,
        "system": "DUMMY_SAP",
    }


def get_dummy_purchase_info_record(info_record_number: str):
    """Retrieve a persisted record by its identifier."""

    with get_connection() as conn:
        row = conn.execute("""
            SELECT record_json
            FROM purchase_info_records
            WHERE info_record_number = ?
        """, (info_record_number.strip(),)).fetchone()

    record = _row_to_record(row)

    if not record:
        return {
            "success": False,
            "message": "Purchase Info Record not found.",
            "system": "DUMMY_SAP",
        }

    return {
        "success": True,
        "record": record,
        "system": "DUMMY_SAP",
    }


initialize_database()
