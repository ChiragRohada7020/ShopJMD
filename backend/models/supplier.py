from datetime import datetime, timezone

from bson import ObjectId

from utils.validators import to_float


def validate_supplier_payload(data, partial=False):
    errors = {}
    required_fields = ["supplier_name"]

    if not partial:
        for field in required_fields:
            if not str(data.get(field, "")).strip():
                errors[field] = "This field is required"

    supplier = {}
    if "supplier_name" in data:
        name = str(data.get("supplier_name", "")).strip()
        if not name:
            errors["supplier_name"] = "Supplier name is required"
        supplier["supplier_name"] = name

    if "mobile_number" in data:
        supplier["mobile_number"] = str(data.get("mobile_number", "")).strip()

    if "address" in data:
        supplier["address"] = str(data.get("address", "")).strip()

    if "notes" in data:
        supplier["notes"] = str(data.get("notes", "")).strip()

    if "opening_balance" in data or not partial:
        supplier["opening_balance"] = to_float(data.get("opening_balance", 0))

    return supplier, errors


def create_supplier_document(data):
    now = datetime.now(timezone.utc)
    return {
        "supplier_name": data["supplier_name"],
        "mobile_number": data.get("mobile_number", ""),
        "address": data.get("address", ""),
        "notes": data.get("notes", ""),
        "opening_balance": data.get("opening_balance", 0),
        "created_at": now,
        "updated_at": now,
    }


def serialize_supplier(supplier, balance=None):
    if not supplier:
        return None

    result = {
        "id": str(supplier["_id"]),
        "supplier_name": supplier.get("supplier_name", ""),
        "mobile_number": supplier.get("mobile_number", ""),
        "address": supplier.get("address", ""),
        "notes": supplier.get("notes", ""),
        "opening_balance": float(supplier.get("opening_balance", 0)),
        "created_at": supplier.get("created_at").isoformat() if supplier.get("created_at") else "",
        "updated_at": supplier.get("updated_at").isoformat() if supplier.get("updated_at") else "",
    }
    if balance is not None:
        result["balance"] = float(balance)
    return result


def supplier_object_id(supplier_id):
    return ObjectId(str(supplier_id))
