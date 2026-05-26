from bson import ObjectId

from models.transaction import serialize_transaction


def supplier_totals(db, supplier_id):
    pipeline = [
        {"$match": {"supplier_id": ObjectId(str(supplier_id))}},
        {
            "$group": {
                "_id": "$transaction_type",
                "total": {"$sum": "$amount"},
            }
        },
    ]
    totals = {"credit": 0, "debit": 0}
    for row in db.transactions.aggregate(pipeline):
        totals[row["_id"]] = float(row.get("total", 0))
    return totals


def supplier_balance(db, supplier):
    totals = supplier_totals(db, supplier["_id"])
    return float(supplier.get("opening_balance", 0)) + totals["credit"] - totals["debit"]


def transactions_with_running_balance(db, supplier):
    balance = float(supplier.get("opening_balance", 0))
    rows = []
    cursor = db.transactions.find({"supplier_id": supplier["_id"]}).sort([("date", 1), ("created_at", 1)])
    for transaction in cursor:
        amount = float(transaction.get("amount", 0))
        if transaction.get("transaction_type") == "credit":
            balance += amount
        else:
            balance -= amount
        rows.append(serialize_transaction(transaction, balance))
    return rows
