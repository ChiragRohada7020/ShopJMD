import json
import re
from datetime import date

from flask import current_app
from groq import Groq


SYSTEM_PROMPT = """
You parse Hindi, Hinglish, and Indian shop ledger voice text into strict JSON.
Return only valid JSON with keys:
supplier_name, transaction_type, quantity, unit, rate, amount, date, description.
transaction_type must be "credit" or "debit".
If amount is missing and quantity/rate exist, amount = quantity * rate.
If date is missing use the provided current date.
Do not invent a supplier name if none is spoken.
If a spoken supplier name sounds close to one of the known suppliers, choose the closest known supplier name.
"""


def parse_voice_with_groq(text, supplier_names=None):
    supplier_names = supplier_names or []
    today = date.today().isoformat()
    api_key = current_app.config.get("GROQ_API_KEY", "")
    model = current_app.config.get("GROQ_MODEL", "llama3-70b-8192")

    if not api_key or api_key == "your_key":
        return fallback_parse(text, today, supplier_names)

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "current_date": today,
                            "known_suppliers": supplier_names,
                            "voice_text": text,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return normalize_ai_payload(json.loads(content), text, today)
    except Exception as error:
        current_app.logger.warning("Groq voice parsing failed, using fallback parser: %s", error)
        return fallback_parse(text, today, supplier_names)


def fallback_parse(text, today, supplier_names=None):
    lower = text.lower()
    numbers = [float(match) for match in re.findall(r"\d+(?:\.\d+)?", lower)]
    quantity = numbers[0] if numbers else 0
    rate = numbers[1] if len(numbers) > 1 else 0
    amount = quantity * rate if quantity and rate else (numbers[0] if numbers else 0)
    unit_match = re.search(r"\b(katta|katter|bag|bags|kg|kilo|quintal|piece|pcs|box|packet)\b", lower)
    unit = unit_match.group(1) if unit_match else ""
    transaction_type = "credit" if "credit" in lower or "se" in lower else "debit"
    supplier_name = ""

    for name in supplier_names or []:
        if name.lower() in lower:
            supplier_name = name
            break

    if not supplier_name:
        match = re.search(r"\b([\w]+)\s+(supplier|ko|se|को|से)\b", text, flags=re.IGNORECASE)
        supplier_name = match.group(1) if match else ""

    return normalize_ai_payload(
        {
            "supplier_name": supplier_name,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "unit": unit,
            "rate": rate,
            "amount": amount,
            "date": today,
            "description": text,
        },
        text,
        today,
    )


def normalize_ai_payload(payload, original_text, today):
    quantity = safe_float(payload.get("quantity"))
    rate = safe_float(payload.get("rate"))
    amount = safe_float(payload.get("amount"))
    if amount <= 0 and quantity > 0 and rate > 0:
        amount = quantity * rate

    transaction_type = str(payload.get("transaction_type", "")).lower()
    if transaction_type not in {"credit", "debit"}:
        transaction_type = "debit"

    return {
        "supplier_name": str(payload.get("supplier_name", "")).strip(),
        "transaction_type": transaction_type,
        "quantity": quantity,
        "unit": str(payload.get("unit", "")).strip(),
        "rate": rate,
        "amount": amount,
        "date": str(payload.get("date") or today)[:10],
        "description": str(payload.get("description") or original_text).strip(),
    }


def safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0
