from datetime import datetime, timezone

from bson import ObjectId

from utils.validators import to_date_string, to_float


VALID_TRANSACTION_TYPES = {"credit", "debit"}


def validate_transaction_payload(data):
    errors = {}
    supplier_id = str(data.get("supplier_id", "")).strip()
    transaction_type = str(data.get("transaction_type", "")).lower().strip()

    if not ObjectId.is_valid(supplier_id):
        errors["supplier_id"] = "Valid supplier ID is required"
    if transaction_type not in VALID_TRANSACTION_TYPES:
        errors["transaction_type"] = "Transaction type must be credit or debit"

    quantity = to_float(data.get("quantity", 0))
    rate = to_float(data.get("rate", 0))
    amount = to_float(data.get("amount", 0))
    weight_per_unit = to_float(data.get("weight_per_unit", 0))
    total_weight = to_float(data.get("total_weight", 0))
    if amount <= 0 and quantity > 0 and rate > 0:
        amount = quantity * rate
    if total_weight <= 0 and quantity > 0 and weight_per_unit > 0:
        total_weight = quantity * weight_per_unit

    try:
        tx_date = to_date_string(data.get("date"))
    except ValueError as exc:
        errors["date"] = str(exc)
        tx_date = to_date_string()

    if amount <= 0:
        errors["amount"] = "Amount must be greater than zero"

    transaction = {
        "supplier_id": ObjectId(supplier_id) if ObjectId.is_valid(supplier_id) else supplier_id,
        "supplier_name": str(data.get("supplier_name", "")).strip(),
        "transaction_type": transaction_type,
        "product_name": str(data.get("product_name", "")).strip(),
        "quantity": quantity,
        "unit": str(data.get("unit", "")).strip() or "unit",
        "weight_per_unit": weight_per_unit,
        "weight_unit": str(data.get("weight_unit", "")).strip(),
        "total_weight": total_weight,
        "rate": rate,
        "rate_type": str(data.get("rate_type", "")).strip(),
        "amount": amount,
        "payment_type": str(data.get("payment_type", "")).strip(),
        "confidence": to_float(data.get("confidence", 0)),
        "needs_confirmation": bool(data.get("needs_confirmation", False)),
        "uncertain_fields": data.get("uncertain_fields", []),
        "normalized_text": str(data.get("normalized_text", "")).strip(),
        "description": str(data.get("description", "")).strip(),
        "date": tx_date,
    }

    return transaction, errors


def create_transaction_document(data, supplier):
    now = datetime.now(timezone.utc)
    description = data.get("description") or (
        f"{data['quantity']:g} {data['unit']} at {data['rate']:g}"
        if data.get("quantity") and data.get("rate")
        else data["transaction_type"].title()
    )

    return {
        **data,
        "supplier_name": supplier.get("supplier_name", data.get("supplier_name", "")),
        "description": description,
        "created_at": now,
        "updated_at": now,
    }


def serialize_transaction(transaction, balance=None):
    if not transaction:
        return None

    result = {
        "id": str(transaction["_id"]),
        "supplier_id": str(transaction.get("supplier_id", "")),
        "supplier_name": transaction.get("supplier_name", ""),
        "transaction_type": transaction.get("transaction_type", ""),
        "product_name": transaction.get("product_name", ""),
        "quantity": float(transaction.get("quantity", 0)),
        "unit": transaction.get("unit", ""),
        "weight_per_unit": float(transaction.get("weight_per_unit", 0)),
        "weight_unit": transaction.get("weight_unit", ""),
        "total_weight": float(transaction.get("total_weight", 0)),
        "rate": float(transaction.get("rate", 0)),
        "rate_type": transaction.get("rate_type", ""),
        "amount": float(transaction.get("amount", 0)),
        "payment_type": transaction.get("payment_type", ""),
        "confidence": float(transaction.get("confidence", 0)),
        "needs_confirmation": bool(transaction.get("needs_confirmation", False)),
        "uncertain_fields": transaction.get("uncertain_fields", []),
        "normalized_text": transaction.get("normalized_text", ""),
        "description": transaction.get("description", ""),
        "date": transaction.get("date", ""),
        "created_at": transaction.get("created_at").isoformat() if transaction.get("created_at") else "",
    }
    if balance is not None:
        result["balance"] = float(balance)
    return result
