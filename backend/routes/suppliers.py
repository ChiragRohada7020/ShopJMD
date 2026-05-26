from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, jsonify, request

from models.supplier import create_supplier_document, serialize_supplier, validate_supplier_payload
from services.db import get_db, suppliers_collection, transactions_collection
from services.ledger_service import supplier_balance


suppliers_bp = Blueprint("suppliers", __name__)


@suppliers_bp.post("")
def create_supplier():
    db = get_db()
    suppliers = suppliers_collection(db)
    payload = request.get_json(silent=True) or {}
    supplier_data, errors = validate_supplier_payload(payload)
    if errors:
        return jsonify({"errors": errors}), 400

    document = create_supplier_document(supplier_data)
    result = suppliers.insert_one(document)
    created = suppliers.find_one({"_id": result.inserted_id})
    return jsonify({"supplier": serialize_supplier(created, supplier_balance(db, created))}), 201


@suppliers_bp.get("")
def list_suppliers():
    db = get_db()
    suppliers = suppliers_collection(db)
    search = request.args.get("search", "").strip()
    query = {}
    if search:
        query = {"supplier_name": {"$regex": search, "$options": "i"}}

    supplier_rows = []
    for supplier in suppliers.find(query).sort("created_at", -1):
        supplier_rows.append(serialize_supplier(supplier, supplier_balance(db, supplier)))
    return jsonify({"suppliers": supplier_rows})


@suppliers_bp.get("/<supplier_id>")
def get_supplier(supplier_id):
    db = get_db()
    suppliers = suppliers_collection(db)
    if not ObjectId.is_valid(supplier_id):
        return jsonify({"error": "Invalid supplier ID"}), 400

    supplier = suppliers.find_one({"_id": ObjectId(supplier_id)})
    if not supplier:
        return jsonify({"error": "Supplier not found"}), 404
    return jsonify({"supplier": serialize_supplier(supplier, supplier_balance(db, supplier))})


@suppliers_bp.put("/<supplier_id>")
def update_supplier(supplier_id):
    db = get_db()
    suppliers = suppliers_collection(db)
    transactions = transactions_collection(db)
    if not ObjectId.is_valid(supplier_id):
        return jsonify({"error": "Invalid supplier ID"}), 400

    payload = request.get_json(silent=True) or {}
    supplier_data, errors = validate_supplier_payload(payload, partial=True)
    if errors:
        return jsonify({"errors": errors}), 400
    if not supplier_data:
        return jsonify({"error": "Nothing to update"}), 400

    supplier_data["updated_at"] = datetime.now(timezone.utc)
    result = suppliers.update_one({"_id": ObjectId(supplier_id)}, {"$set": supplier_data})
    if result.matched_count == 0:
        return jsonify({"error": "Supplier not found"}), 404

    if "supplier_name" in supplier_data:
        transactions.update_many(
            {"supplier_id": ObjectId(supplier_id)},
            {"$set": {"supplier_name": supplier_data["supplier_name"], "updated_at": supplier_data["updated_at"]}},
        )

    supplier = suppliers.find_one({"_id": ObjectId(supplier_id)})
    return jsonify({"supplier": serialize_supplier(supplier, supplier_balance(db, supplier))})


@suppliers_bp.delete("/<supplier_id>")
def delete_supplier(supplier_id):
    db = get_db()
    suppliers = suppliers_collection(db)
    transactions = transactions_collection(db)
    if not ObjectId.is_valid(supplier_id):
        return jsonify({"error": "Invalid supplier ID"}), 400

    supplier_object_id = ObjectId(supplier_id)
    result = suppliers.delete_one({"_id": supplier_object_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Supplier not found"}), 404

    transactions.delete_many({"supplier_id": supplier_object_id})
    return jsonify({"message": "Supplier and related transactions deleted"})
