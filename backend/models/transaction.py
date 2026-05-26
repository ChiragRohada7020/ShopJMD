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
    if amount <= 0 and quantity > 0 and rate > 0:
        amount = quantity * rate

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
        "quantity": quantity,
        "unit": str(data.get("unit", "")).strip() or "unit",
        "rate": rate,
        "amount": amount,
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
        "quantity": float(transaction.get("quantity", 0)),
        "unit": transaction.get("unit", ""),
        "rate": float(transaction.get("rate", 0)),
        "amount": float(transaction.get("amount", 0)),
        "description": transaction.get("description", ""),
        "date": transaction.get("date", ""),
        "created_at": transaction.get("created_at").isoformat() if transaction.get("created_at") else "",
    }
    if balance is not None:
        result["balance"] = float(balance)
    return result
