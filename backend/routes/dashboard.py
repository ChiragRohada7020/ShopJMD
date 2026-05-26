from flask import Blueprint, jsonify

from models.transaction import serialize_transaction
from services.db import get_db


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/dashboard")
def dashboard():
    db = get_db()
    total_suppliers = db.suppliers.count_documents({})

    totals = {"credit": 0, "debit": 0}
    pipeline = [{"$group": {"_id": "$transaction_type", "total": {"$sum": "$amount"}}}]
    for row in db.transactions.aggregate(pipeline):
        totals[row["_id"]] = float(row.get("total", 0))

    opening_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$opening_balance"}}}]
    opening_rows = list(db.suppliers.aggregate(opening_pipeline))
    opening_balance = float(opening_rows[0]["total"]) if opening_rows else 0

    recent = [
        serialize_transaction(transaction)
        for transaction in db.transactions.find({}).sort("created_at", -1).limit(8)
    ]

    return jsonify(
        {
            "total_suppliers": total_suppliers,
            "total_credit": totals["credit"],
            "total_debit": totals["debit"],
            "net_balance": opening_balance + totals["credit"] - totals["debit"],
            "recent_transactions": recent,
        }
    )
