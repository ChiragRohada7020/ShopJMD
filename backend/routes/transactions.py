from bson import ObjectId
from flask import Blueprint, jsonify, request

from models.transaction import create_transaction_document, serialize_transaction, validate_transaction_payload
from services.db import get_db
from services.ledger_service import transactions_with_running_balance


transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.post("/transactions")
def create_transaction():
    db = get_db()
    payload = request.get_json(silent=True) or {}
    transaction_data, errors = validate_transaction_payload(payload)
    if errors:
        return jsonify({"errors": errors}), 400

    supplier = db.suppliers.find_one({"_id": transaction_data["supplier_id"]})
    if not supplier:
        return jsonify({"error": "Supplier not found"}), 404

    document = create_transaction_document(transaction_data, supplier)
    result = db.transactions.insert_one(document)
    created = db.transactions.find_one({"_id": result.inserted_id})
    return jsonify({"transaction": serialize_transaction(created)}), 201


@transactions_bp.get("/transactions")
def list_transactions():
    db = get_db()
    supplier_id = request.args.get("supplier_id")
    query = {}
    if supplier_id:
        if not ObjectId.is_valid(supplier_id):
            return jsonify({"error": "Invalid supplier ID"}), 400
        query["supplier_id"] = ObjectId(supplier_id)

    transactions = [
        serialize_transaction(transaction)
        for transaction in db.transactions.find(query).sort([("date", -1), ("created_at", -1)])
    ]
    return jsonify({"transactions": transactions})


@transactions_bp.get("/suppliers/<supplier_id>/transactions")
def supplier_transactions(supplier_id):
    db = get_db()
    if not ObjectId.is_valid(supplier_id):
        return jsonify({"error": "Invalid supplier ID"}), 400

    supplier = db.suppliers.find_one({"_id": ObjectId(supplier_id)})
    if not supplier:
        return jsonify({"error": "Supplier not found"}), 404

    return jsonify({"transactions": transactions_with_running_balance(db, supplier)})
