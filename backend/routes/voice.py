from flask import Blueprint, jsonify, request

from models.supplier import create_supplier_document
from services.db import get_db, suppliers_collection
from services.groq_service import parse_voice_with_groq
from services.supplier_matcher import find_best_supplier_match


voice_bp = Blueprint("voice", __name__)


@voice_bp.post("/parse-voice")
def parse_voice():
    db = get_db()
    suppliers = suppliers_collection(db)
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify({"error": "Voice text is required"}), 400

    supplier_rows = list(suppliers.find({}, {"supplier_name": 1}))
    supplier_names = [row["supplier_name"] for row in supplier_rows]
    parsed = parse_voice_with_groq(text, supplier_names)

    matched_supplier, match_score = find_best_supplier_match(supplier_rows, parsed.get("supplier_name", ""), text)
    if matched_supplier:
        parsed["original_supplier_name"] = parsed.get("supplier_name", "")
        parsed["supplier_id"] = str(matched_supplier["_id"])
        parsed["supplier_name"] = matched_supplier["supplier_name"]
        parsed["supplier_match_score"] = match_score
        parsed["supplier_match_type"] = "matched"
    elif can_create_supplier_from_voice(parsed.get("supplier_name", "")):
        supplier_name = clean_supplier_name(parsed["supplier_name"])
        document = create_supplier_document(
            {
                "supplier_name": supplier_name,
                "mobile_number": "",
                "address": "",
                "notes": "Auto-created from voice entry",
                "opening_balance": 0,
            }
        )
        result = suppliers.insert_one(document)
        parsed["supplier_id"] = str(result.inserted_id)
        parsed["supplier_name"] = supplier_name
        parsed["supplier_match_score"] = 1
        parsed["supplier_match_type"] = "created"

    return jsonify({"parsed": parsed})


def clean_supplier_name(value):
    return " ".join(str(value or "").strip().split())


def can_create_supplier_from_voice(value):
    name = clean_supplier_name(value)
    if len(name) < 2:
        return False
    if name.lower() in {"supplier", "debit", "credit", "cash", "unknown"}:
        return False
    return any(character.isalpha() for character in name)
