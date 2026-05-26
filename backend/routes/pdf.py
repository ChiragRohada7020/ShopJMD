from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request, send_file

from services.db import get_db, suppliers_collection
from services.pdf_service import build_supplier_ledger_pdf


pdf_bp = Blueprint("pdf", __name__)


@pdf_bp.get("/<supplier_id>/pdf")
def supplier_pdf(supplier_id):
    db = get_db()
    suppliers = suppliers_collection(db)
    if not ObjectId.is_valid(supplier_id):
        return jsonify({"error": "Invalid supplier ID"}), 400

    supplier = suppliers.find_one({"_id": ObjectId(supplier_id)})
    if not supplier:
        return jsonify({"error": "Supplier not found"}), 404

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    pdf_buffer = build_supplier_ledger_pdf(
        db,
        supplier,
        current_app.config["SHOP_NAME"],
        start_date=start_date,
        end_date=end_date,
    )
    filename = f"{supplier.get('supplier_name', 'supplier')}-ledger.pdf".replace(" ", "-")
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")
