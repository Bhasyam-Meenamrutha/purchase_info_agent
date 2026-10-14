
import os

from dotenv import load_dotenv

from . import dummy_sap

load_dotenv()

BACKEND = os.getenv("PURCHASE_INFO_BACKEND", "dummy").lower()


def find_purchase_info_record(
    supplier: str,
    material: str,
    purchasing_organization: str,
    info_record_category: str = "STANDARD",
):
    """Find a Purchase Info Record using the selected backend."""

    if BACKEND == "dummy":
        return dummy_sap.find_purchase_info_record(
            supplier=supplier,
            material=material,
            purchasing_organization=purchasing_organization,
            info_record_category=info_record_category,
        )

    raise NotImplementedError(
        f"Backend '{BACKEND}' is not implemented yet."
    )


def create_purchase_info_record_backend(data: dict):
    """Create a record through the selected backend."""

    if BACKEND == "dummy":
        return dummy_sap.create_dummy_purchase_info_record(data)

    raise NotImplementedError(
        f"Backend '{BACKEND}' is not implemented yet."
    )


def get_purchase_info_record_backend(info_record_number: str):
    """Retrieve a record through the selected backend."""

    if BACKEND == "dummy":
        return dummy_sap.get_dummy_purchase_info_record(
            info_record_number
        )

    raise NotImplementedError(
        f"Backend '{BACKEND}' is not implemented yet."
    )
