
from .purchase_info_service import (
    find_purchase_info_record,
    create_purchase_info_record_backend,
    get_purchase_info_record_backend,
)


def check_existing_purchase_info_record(
    supplier: str,
    material: str,
    purchasing_organization: str,
    info_record_category: str = "STANDARD",
) -> dict:
    """Check whether a matching Purchase Info Record exists."""

    record = find_purchase_info_record(
        supplier=supplier.strip(),
        material=material.strip(),
        purchasing_organization=purchasing_organization.strip(),
        info_record_category=info_record_category.strip().upper(),
    )

    if record:
        return {
            "success": True,
            "exists": True,
            "record": record,
            "message": "A matching Purchase Info Record exists.",
            "system": record.get("system", "DUMMY_SAP"),
        }

    return {
        "success": True,
        "exists": False,
        "message": "No matching Purchase Info Record was found.",
    }


def prepare_purchase_info_record(
    supplier: str,
    material: str,
    purchasing_organization: str,
    net_price: float,
    currency: str = "INR",
    plant: str = "",
    order_unit: str = "EA",
    planned_delivery_time: int = 7,
    info_record_category: str = "STANDARD",
) -> dict:
    """Validate and prepare a record without creating it."""

    # Validate required string fields.
    required_fields = {
        "supplier": supplier,
        "material": material,
        "purchasing_organization": purchasing_organization,
        "currency": currency,
        "order_unit": order_unit,
        "info_record_category": info_record_category,
    }

    for field_name, value in required_fields.items():
        if not isinstance(value, str) or not value.strip():
            return {
                "success": False,
                "message": f"{field_name.replace('_', ' ').title()} is required.",
            }

    # Reject invalid numeric values.
    if isinstance(net_price, bool) or not isinstance(
        net_price, (int, float)
    ):
        return {
            "success": False,
            "message": "Net price must be a valid number.",
        }

    if net_price <= 0:
        return {
            "success": False,
            "message": "Net price must be greater than zero.",
        }

    if isinstance(planned_delivery_time, bool) or not isinstance(
        planned_delivery_time, int
    ):
        return {
            "success": False,
            "message": "Planned delivery time must be a whole number.",
        }

    if planned_delivery_time < 0:
        return {
            "success": False,
            "message": "Planned delivery time cannot be negative.",
        }

    if len(currency.strip()) != 3:
        return {
            "success": False,
            "message": "Currency must be a three-letter code.",
        }

    category = info_record_category.strip().upper()

    if category != "STANDARD":
        return {
            "success": False,
            "message": (
                "The dummy POC currently supports STANDARD records only."
            ),
        }

    # Normalize the data before checking for duplicates.
    data = {
        "supplier": supplier.strip(),
        "material": material.strip(),
        "purchasing_organization": purchasing_organization.strip(),
        "plant": plant.strip(),
        "net_price": float(net_price),
        "currency": currency.strip().upper(),
        "order_unit": order_unit.strip().upper(),
        "planned_delivery_time": planned_delivery_time,
        "info_record_category": category,
    }

    # Check whether the business key already exists.
    existing = find_purchase_info_record(
        supplier=data["supplier"],
        material=data["material"],
        purchasing_organization=data["purchasing_organization"],
        info_record_category=data["info_record_category"],
    )

    if existing:
        return {
            "success": False,
            "exists": True,
            "message": "A matching Purchase Info Record already exists.",
            "existing_record": existing,
        }

    return {
        "success": True,
        "requires_confirmation": True,
        "confirmation_phrase": "CONFIRM CREATE",
        "system": "DUMMY_SAP",
        "message": (
            "The request passed the current dummy validation rules. "
            "Review the proposed details before confirming. "
            "No record has been created."
        ),
        "record_to_create": data,
    }


def create_purchase_info_record(
    supplier: str,
    material: str,
    purchasing_organization: str,
    net_price: float,
    currency: str,
    plant: str,
    order_unit: str,
    planned_delivery_time: int,
    confirmation_phrase: str,
    info_record_category: str = "STANDARD",
) -> dict:
    """Create a record through the configured backend.

    The current backend is DUMMY_SAP. This does not create a real
    SAP record.

    Call only after the user explicitly confirms the proposed record.
    """

    if not isinstance(confirmation_phrase, str):
        return {
            "success": False,
            "message": "A valid confirmation phrase is required.",
            "system": "DUMMY_SAP",
        }

    if confirmation_phrase.strip() != "CONFIRM CREATE":
        return {
            "success": False,
            "message": (
                "Creation was not confirmed. Ask the user to review "
                "the record and enter CONFIRM CREATE."
            ),
            "system": "DUMMY_SAP",
        }

    # Reuse the preparation tool's validation rules.
    prepared = prepare_purchase_info_record(
        supplier=supplier,
        material=material,
        purchasing_organization=purchasing_organization,
        net_price=net_price,
        currency=currency,
        plant=plant,
        order_unit=order_unit,
        planned_delivery_time=planned_delivery_time,
        info_record_category=info_record_category,
    )

    if not prepared.get("success"):
        return prepared

    if prepared.get("exists"):
        return prepared

    data = prepared["record_to_create"]

    # Delegate creation to the selected backend.
    result = create_purchase_info_record_backend(data)

    if result.get("success"):
        return {
            **result,
            "message": "Purchase Info Record created successfully.",
        }

    return result


def get_purchase_info_record(
    info_record_number: str,
) -> dict:
    """Retrieve a record by its identifier."""

    if not isinstance(info_record_number, str) or not info_record_number.strip():
        return {
            "success": False,
            "message": "Info Record Number is required.",
        }

    return get_purchase_info_record_backend(
        info_record_number.strip()
    )
