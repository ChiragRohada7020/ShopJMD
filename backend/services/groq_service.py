import json
import re
from difflib import get_close_matches
from datetime import date

from flask import current_app
from groq import Groq


SYSTEM_PROMPT = """
You parse Hindi, Hinglish, and Indian shop ledger voice text into strict JSON for a supplier ledger app.
Return only valid JSON with keys:
supplier_name, product_name, transaction_type, quantity, unit, weight_per_unit, weight_unit, total_weight, rate, rate_type, amount, payment_type, date, description, confidence, uncertain_fields.
transaction_type must be "credit" or "debit".
rate_type must be one of: "per_kg", "per_unit", "total", "unknown".
payment_type must be one of: "cash", "ledger", "unknown".
Use the Indian shop ledger meaning from ledger_examples exactly. These examples are more important than English accounting assumptions.
For goods phrases, segregate spoken parts into fields. Example: "bh ka teen kaate 30 kilo ke 500 rupaye me" means supplier_name "bh", quantity 3, unit "katta (30 kg)", rate 500, amount 1500.
Common retailer units include goni, daag, katta/kaata, carton/catoon, set, nag, bori, bag, packet, box, kg, kilo.
Mobile speech may join quantity and unit into one word, such as dogoni = do goni, teenkaata = teen kaata, dokaata = do kaata, donag = do nag. Split these before parsing.
Understand Hindi/Marathi money words: sau/sao/so means hundred, hazar/hajaar means thousand, and tevis/tavis sao means 2300.
Use corrected_voice_text to fix common voice spelling mistakes, but keep the user's original meaning.
If text starts with a supplier code/name followed by a product word, such as "bh shakkar ki doguni 1322 mili", supplier_name is "bh" and product is not supplier.
If a goods phrase has no clear cash received/paid word, default transaction_type to "debit".
If phrase says per kg/kg bhav, amount = quantity * kg-per-unit * rate. If it says only "45 ka bhav" without per kg, amount = quantity * rate.
If amount is missing and quantity/rate exist, amount = quantity * rate unless per kg rule applies.
If date is missing use the provided current date.
Do not invent a supplier name if none is spoken.
If a spoken supplier name sounds close to one of the known suppliers, choose the closest known supplier name.
"""

LEDGER_EXAMPLES = [
    {
        "voice_text": "ramesh ke khate me 2000 jama karo",
        "transaction_type": "credit",
        "meaning": "Money is added/received into Ramesh account.",
    },
    {
        "voice_text": "ramesh account me 2000 jama",
        "transaction_type": "credit",
        "meaning": "Deposit/payment received in Ramesh account.",
    },
    {
        "voice_text": "ramesh se 2000 liye",
        "transaction_type": "credit",
        "meaning": "Money received from Ramesh.",
    },
    {
        "voice_text": "ramesh ko 2000 diye",
        "transaction_type": "debit",
        "meaning": "Money paid/given to Ramesh.",
    },
    {
        "voice_text": "ramesh ko rokad diye 2000",
        "transaction_type": "debit",
        "meaning": "Cash paid/given to Ramesh.",
    },
    {
        "voice_text": "ramesh ko rok diye 2000",
        "transaction_type": "debit",
        "meaning": "Mobile speech may hear rokad as rok; treat as cash given.",
    },
    {
        "voice_text": "bh ka teen kaate 30 kilo ke 500 rupaye me",
        "parsed": {
            "supplier_name": "bh",
            "transaction_type": "debit",
            "quantity": 3,
            "unit": "katta (30 kg)",
            "rate": 500,
            "amount": 1500,
            "description": "3 katta, 30 kg each, at 500",
        },
    },
    {
        "voice_text": "ramesh ke 2 katta 50 kilo ke 900 rupaye rate par",
        "parsed": {
            "supplier_name": "ramesh",
            "transaction_type": "debit",
            "quantity": 2,
            "unit": "katta (50 kg)",
            "rate": 900,
            "amount": 1800,
            "description": "2 katta, 50 kg each, at 900",
        },
    },
    {
        "voice_text": "shyam se 4 bag 25 kg ke 700 me liye",
        "parsed": {
            "supplier_name": "shyam",
            "transaction_type": "credit",
            "quantity": 4,
            "unit": "bag (25 kg)",
            "rate": 700,
            "amount": 2800,
            "description": "4 bag, 25 kg each, at 700",
        },
    },
    {
        "voice_text": "sugar ki do goni",
        "parsed": {
            "supplier_name": "",
            "transaction_type": "debit",
            "quantity": 2,
            "unit": "goni",
            "rate": 0,
            "amount": 0,
            "description": "sugar, 2 goni",
        },
    },
    {
        "voice_text": "sugar ki dogoni 1500 rupaye me",
        "parsed": {
            "supplier_name": "",
            "transaction_type": "debit",
            "quantity": 2,
            "unit": "goni",
            "rate": 1500,
            "amount": 3000,
            "description": "sugar, 2 goni, at 1500",
        },
    },
    {
        "voice_text": "sugar ki dogoni tavis sao rupaye me",
        "parsed": {
            "supplier_name": "",
            "transaction_type": "debit",
            "quantity": 2,
            "unit": "goni",
            "rate": 2300,
            "amount": 4600,
            "description": "sugar, 2 goni, at 2300",
        },
    },
    {
        "voice_text": "bh shakkar ki doguni 1322 mili",
        "parsed": {
            "supplier_name": "bh",
            "transaction_type": "credit",
            "quantity": 2,
            "unit": "goni",
            "rate": 1322,
            "amount": 2644,
            "description": "shakkar, 2 goni, at 1322",
        },
    },
    {
        "voice_text": "shakkar ki do goni 50 kilo ki 45 per kg ka bhav",
        "parsed": {
            "supplier_name": "",
            "transaction_type": "debit",
            "quantity": 2,
            "unit": "goni (50 kg)",
            "rate": 45,
            "amount": 4500,
            "description": "sugar, 2 goni (50 kg), at 45 per kg",
        },
    },
    {
        "voice_text": "shakkar ki do goni 50 kilo ki 45 ka bhav",
        "parsed": {
            "supplier_name": "",
            "transaction_type": "debit",
            "quantity": 2,
            "unit": "goni (50 kg)",
            "rate": 45,
            "amount": 90,
            "description": "sugar, 2 goni (50 kg), at 45",
        },
    },
]

SPOKEN_NUMBERS = {
    "zero": 0,
    "ek": 1,
    "aek": 1,
    "one": 1,
    "do": 2,
    "two": 2,
    "teen": 3,
    "tin": 3,
    "three": 3,
    "char": 4,
    "chaar": 4,
    "four": 4,
    "panch": 5,
    "paanch": 5,
    "five": 5,
    "che": 6,
    "chhe": 6,
    "six": 6,
    "saat": 7,
    "seven": 7,
    "aath": 8,
    "eight": 8,
    "nau": 9,
    "nine": 9,
    "das": 10,
    "ten": 10,
    "gyarah": 11,
    "akra": 11,
    "eleven": 11,
    "barah": 12,
    "bara": 12,
    "twelve": 12,
    "terah": 13,
    "tera": 13,
    "thirteen": 13,
    "chaudah": 14,
    "chauda": 14,
    "fourteen": 14,
    "pandrah": 15,
    "pandra": 15,
    "fifteen": 15,
    "solah": 16,
    "sola": 16,
    "sixteen": 16,
    "satrah": 17,
    "satra": 17,
    "seventeen": 17,
    "atharah": 18,
    "athra": 18,
    "eighteen": 18,
    "unnis": 19,
    "unish": 19,
    "nineteen": 19,
    "bees": 20,
    "bis": 20,
    "twenty": 20,
    "ikkis": 21,
    "ekvis": 21,
    "twentyone": 21,
    "bais": 22,
    "bavis": 22,
    "twentytwo": 22,
    "teis": 23,
    "tevis": 23,
    "tavis": 23,
    "twentythree": 23,
    "chaubis": 24,
    "chovis": 24,
    "twentyfour": 24,
    "pachis": 25,
    "panchvis": 25,
    "twentyfive": 25,
    "chabbis": 26,
    "savvis": 26,
    "twentysix": 26,
    "sattais": 27,
    "sattavis": 27,
    "twentyseven": 27,
    "athais": 28,
    "athavis": 28,
    "twentyeight": 28,
    "untis": 29,
    "unatis": 29,
    "twentynine": 29,
    "tees": 30,
    "tis": 30,
    "thirty": 30,
}

UNIT_ALIASES = {
    "goni": "goni",
    "gonia": "goni",
    "guni": "goni",
    "gunny": "goni",
    "bora": "bora",
    "bore": "bora",
    "bori": "bori",
    "bory": "bori",
    "peti": "peti",
    "pety": "peti",
    "daag": "daag",
    "dag": "daag",
    "katta": "katta",
    "katte": "katta",
    "kattae": "katta",
    "kaata": "katta",
    "kaate": "katta",
    "kate": "katta",
    "katter": "katta",
    "carton": "carton",
    "cartoon": "carton",
    "catoon": "carton",
    "set": "set",
    "nag": "nag",
    "nug": "nag",
    "bag": "bag",
    "bags": "bag",
    "kg": "kg",
    "kilo": "kg",
    "quintal": "quintal",
    "piece": "piece",
    "pcs": "piece",
    "box": "box",
    "packet": "packet",
    "pouch": "packet",
    "thaila": "thaila",
    "thela": "thaila",
    "dabba": "dabba",
    "daba": "dabba",
    "liter": "litre",
    "litre": "litre",
    "ltr": "litre",
    "gram": "gram",
    "gm": "gram",
}

PRODUCT_ALIASES = {
    "sugar": "Sugar",
    "shakkar": "Sugar",
    "sakkar": "Sugar",
    "sakhar": "Sugar",
    "sygar": "Sugar",
    "suger": "Sugar",
    "chini": "Sugar",
    "chinni": "Sugar",
    "chawal": "Rice",
    "rice": "Rice",
    "tandul": "Rice",
    "gehu": "Wheat",
    "gehun": "Wheat",
    "gahu": "Wheat",
    "wheat": "Wheat",
    "aam": "Mango",
    "amba": "Mango",
    "mango": "Mango",
    "dal": "Dal",
    "daal": "Dal",
    "oil": "Oil",
    "tel": "Oil",
}
PRODUCT_WORDS = set(PRODUCT_ALIASES)

WORD_CORRECTIONS = {
    "sygar": "sugar",
    "suger": "sugar",
    "shugar": "sugar",
    "shakkar": "sugar",
    "sakkar": "sugar",
    "sakhar": "sugar",
    "chinni": "chini",
    "doguni": "do goni",
    "dogony": "do goni",
    "guni": "goni",
    "gunny": "goni",
    "dag": "daag",
    "kaata": "katta",
    "kaate": "katta",
    "kate": "katta",
    "katter": "katta",
    "cartoon": "carton",
    "catoon": "carton",
    "nug": "nag",
    "bory": "bori",
    "tavis": "tevis",
    "sao": "sau",
    "so": "sau",
    "hajaar": "hazar",
    "hazaar": "hazar",
    "rupya": "rupaye",
    "rupay": "rupaye",
    "rupey": "rupaye",
    "rupee": "rupaye",
    "rupees": "rupaye",
    "perkg": "per kg",
    "parkilo": "per kilo",
    "prkg": "per kg",
    "wale": "wala",
    "udaar": "udhar",
    "udhaari": "udhar",
    "cashh": "cash",
}

FUZZY_VOCABULARY = {
    **{word: word for word in SPOKEN_NUMBERS},
    **UNIT_ALIASES,
    **{word: word for word in PRODUCT_WORDS},
    **WORD_CORRECTIONS,
    "bhav": "bhav",
    "rate": "rate",
    "rupaye": "rupaye",
    "kilo": "kilo",
    "kg": "kg",
    "per": "per",
    "udhar": "udhar",
    "jama": "jama",
    "cash": "cash",
    "diya": "diya",
    "diye": "diye",
    "mila": "mila",
    "mili": "mili",
}

CREDIT_PATTERNS = [
    r"\bcredit\b",
    r"\bjama\b",
    r"\bjma\b",
    r"\bdeposit(?:ed)?\b",
    r"\breceiv(?:e|ed)\b",
    r"\bpayment\s+(?:mila|aaya|aya|received)\b",
    r"\bpaise\s+(?:aaye|aye|aaya|aya|mile|mila)\b",
    r"\b(?:mila|mili|mile|milay)\b",
    r"\b(?:khate|account)\s+(?:me|mein)\s+jama\b",
    r"\bse\b.*\b(?:liye|lia|liya|le\s*liye|le\s*liya|mila|mile)\b",
    r"जमा",
]

DEBIT_PATTERNS = [
    r"\bdebit\b",
    r"\bdebited\b",
    r"\brokad\s+(?:diye|diya|de\s*diye|de\s*diya)\b",
    r"\brokad\b",
    r"\brok\s+(?:diye|diya|de\s*diye|de\s*diya)\b",
    r"\bcash\s+(?:diye|diya|de\s*diye|de\s*diya)\b",
    r"\bpaise\s+(?:diye|diya|de\s*diye|de\s*diya)\b",
    r"\bpayment\s+(?:diye|diya|de\s*diye|de\s*diya|paid)\b",
    r"\bko\b.*\b(?:diye|diya|de\s*diye|de\s*diya)\b",
    r"\budhaar\s+(?:diye|diya|de\s*diye|de\s*diya)\b",
    r"दिए|दिया|डेबिट",
]


def parse_voice_with_groq(text, supplier_names=None):
    supplier_names = supplier_names or []
    today = date.today().isoformat()
    corrected_text = normalize_voice_text(text)
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
                            "ledger_examples": LEDGER_EXAMPLES,
                            "instruction": (
                                "Parse this like a normal Indian retailer speaking quickly. "
                                "Extract supplier, quantity, unit, kg/weight details, rate, amount, and debit/credit. "
                                "Use corrected_voice_text for spelling fixes and ledger_examples as the strongest guide."
                            ),
                            "corrected_voice_text": corrected_text,
                            "voice_text": text,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return normalize_ai_payload(json.loads(content), text, today, corrected_text)
    except Exception as error:
        current_app.logger.warning("Groq voice parsing failed, using fallback parser: %s", error)
        return fallback_parse(text, today, supplier_names)


def fallback_parse(text, today, supplier_names=None):
    corrected_text = normalize_voice_text(text)
    lower = normalize_amount_words(normalize_spoken_numbers(split_joined_quantity_units(corrected_text.lower())))
    numbers = [float(match) for match in re.findall(r"\d+(?:\.\d+)?", lower)]
    unit_words = "|".join(UNIT_ALIASES)
    quantity, unit_word = extract_quantity_and_unit(lower, unit_words)
    rate_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:rupaye|rupees|rs|rate|bhav)\b", lower)
    bhav_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:per\s*(?:kg|kilo)|(?:rupaye\s*)?(?:kg|kilo)|(?:kg|kilo)\s*(?:ka\s*)?bhav|ka\s+bhav)\b", lower)
    weight_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:kg|kilo)\b", lower)

    rate = safe_float(rate_match.group(1)) if rate_match else (safe_float(bhav_match.group(1)) if bhav_match else (numbers[-1] if len(numbers) > 1 else 0))
    amount = calculate_amount(quantity, rate, corrected_text)
    unit = UNIT_ALIASES.get(unit_word, "")
    if unit and weight_match and unit != "kg":
        unit = f"{unit} ({safe_float(weight_match.group(1)):g} kg)"
    transaction_type = detect_transaction_type(text) or "debit"
    product_name = extract_product_name(corrected_text)
    weight_per_unit = safe_float(weight_match.group(1)) if weight_match and unit != "kg" else 0
    rate_type = detect_rate_type(corrected_text)
    payment_type = detect_payment_type(corrected_text)
    supplier_name = ""

    for name in supplier_names or []:
        if name.lower() in lower:
            supplier_name = name
            break

    if not supplier_name:
        match = re.search(r"\b([\w]+)\s+(supplier|ko|se|को|से)\b", text, flags=re.IGNORECASE)
        supplier_name = match.group(1) if match else ""
    if not supplier_name:
        match = re.search(r"\b([\w]+)\s+(ka|ke|ki|account|khate)\b", text, flags=re.IGNORECASE)
        supplier_name = match.group(1) if match else ""
    if supplier_name.lower() in PRODUCT_WORDS:
        supplier_name = ""

    return normalize_ai_payload(
        {
            "supplier_name": supplier_name,
            "product_name": product_name,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "unit": unit,
            "weight_per_unit": weight_per_unit,
            "weight_unit": "kg" if weight_per_unit else "",
            "total_weight": quantity * weight_per_unit if quantity and weight_per_unit else 0,
            "rate": rate,
            "rate_type": rate_type,
            "amount": amount,
            "payment_type": payment_type,
            "date": today,
            "description": text,
        },
        text,
        today,
        corrected_text,
    )


def normalize_ai_payload(payload, original_text, today, corrected_text=None):
    corrected_text = corrected_text or normalize_voice_text(original_text)
    quantity = safe_float(payload.get("quantity"))
    rate = safe_float(payload.get("rate"))
    weight_per_unit = safe_float(payload.get("weight_per_unit")) or extract_weight_per_unit(corrected_text)
    total_weight = safe_float(payload.get("total_weight"))
    if total_weight <= 0 and quantity > 0 and weight_per_unit > 0:
        total_weight = quantity * weight_per_unit
    amount = safe_float(payload.get("amount"))
    calculated_amount = calculate_amount(quantity, rate, corrected_text)
    if calculated_amount > 0:
        amount = calculated_amount
    elif amount <= 0 and quantity > 0 and rate > 0:
        amount = quantity * rate

    transaction_type = str(payload.get("transaction_type", "")).lower()
    if transaction_type not in {"credit", "debit"}:
        transaction_type = "debit"
    transaction_type = detect_transaction_type(original_text) or transaction_type

    supplier_name = str(payload.get("supplier_name", "")).strip()
    supplier_name = correct_supplier_name(supplier_name, corrected_text)
    product_name = normalize_product_name(payload.get("product_name")) or extract_product_name(corrected_text)
    rate_type = str(payload.get("rate_type") or detect_rate_type(corrected_text)).strip() or "unknown"
    payment_type = str(payload.get("payment_type") or detect_payment_type(corrected_text)).strip() or "unknown"
    confidence, uncertain_fields = score_parse_confidence(
        supplier_name=supplier_name,
        product_name=product_name,
        quantity=quantity,
        unit=payload.get("unit"),
        rate=rate,
        amount=amount,
        ai_confidence=safe_float(payload.get("confidence")),
        ai_uncertain_fields=payload.get("uncertain_fields"),
    )
    description = build_clean_description(
        {**payload, "product_name": product_name, "quantity": quantity, "rate": rate},
        original_text,
        corrected_text,
    )

    return {
        "supplier_name": supplier_name,
        "product_name": product_name,
        "transaction_type": transaction_type,
        "quantity": quantity,
        "unit": str(payload.get("unit", "")).strip(),
        "weight_per_unit": weight_per_unit,
        "weight_unit": "kg" if weight_per_unit else str(payload.get("weight_unit", "")).strip(),
        "total_weight": total_weight,
        "rate": rate,
        "rate_type": rate_type if rate_type in {"per_kg", "per_unit", "total", "unknown"} else "unknown",
        "amount": amount,
        "payment_type": payment_type if payment_type in {"cash", "ledger", "unknown"} else "unknown",
        "date": str(payload.get("date") or today)[:10],
        "description": description,
        "confidence": confidence,
        "needs_confirmation": confidence < 0.72 or bool(uncertain_fields),
        "uncertain_fields": uncertain_fields,
        "normalized_text": corrected_text,
    }


def normalize_voice_text(text):
    normalized = str(text or "").lower()
    normalized = split_joined_quantity_units(normalized)
    for wrong, correct in WORD_CORRECTIONS.items():
        normalized = re.sub(rf"\b{wrong}\b", correct, normalized)
    normalized = " ".join(correct_token(token) for token in normalized.split())
    return " ".join(normalized.split())


def correct_token(token):
    clean = re.sub(r"[^a-z0-9.]", "", token.lower())
    if not clean or clean.isdigit() or re.fullmatch(r"\d+(?:\.\d+)?", clean):
        return token
    if clean in FUZZY_VOCABULARY:
        return FUZZY_VOCABULARY[clean]
    if len(clean) < 4:
        return token
    match = get_close_matches(clean, FUZZY_VOCABULARY.keys(), n=1, cutoff=0.78)
    return FUZZY_VOCABULARY[match[0]] if match else token


def correct_supplier_name(supplier_name, corrected_text):
    supplier = str(supplier_name or "").strip()
    tokens = str(corrected_text or "").split()
    if not tokens:
        return supplier

    product_indexes = [index for index, token in enumerate(tokens) if token in PRODUCT_WORDS]
    if not product_indexes:
        return "" if supplier.lower() in PRODUCT_WORDS else supplier

    first_product_index = product_indexes[0]
    if supplier.lower() in PRODUCT_WORDS and first_product_index > 0:
        return tokens[0]
    if not supplier and first_product_index > 0:
        return tokens[0]
    return "" if supplier.lower() in PRODUCT_WORDS else supplier


def build_clean_description(payload, original_text, corrected_text=None):
    corrected = corrected_text or normalize_voice_text(original_text)
    product = normalize_product_name(payload.get("product_name")) or extract_product_name(corrected)
    quantity = safe_float(payload.get("quantity"))
    unit = str(payload.get("unit", "")).strip()
    rate = safe_float(payload.get("rate"))

    parts = []
    if product:
        parts.append(product)
    if quantity > 0 and unit:
        parts.append(f"{quantity:g} {unit}")
    elif unit:
        parts.append(unit)
    if rate > 0:
        suffix = " per kg" if is_per_kg_rate(corrected) else ""
        parts.append(f"at {rate:g}{suffix}")

    if parts:
        return ", ".join(parts)
    return str(payload.get("description") or corrected or original_text).strip()


def calculate_amount(quantity, rate, text):
    if quantity <= 0 or rate <= 0:
        return 0
    weight = extract_weight_per_unit(text)
    if is_per_kg_rate(text) and weight > 0:
        return quantity * weight * rate
    return quantity * rate


def normalize_product_name(value):
    value = str(value or "").strip().lower()
    if not value:
        return ""
    if value in PRODUCT_ALIASES:
        return PRODUCT_ALIASES[value]
    match = get_close_matches(value, PRODUCT_ALIASES.keys(), n=1, cutoff=0.78)
    return PRODUCT_ALIASES[match[0]] if match else str(value).title()


def extract_product_name(text):
    tokens = str(text or "").lower().split()
    for token in tokens:
        if token in PRODUCT_ALIASES:
            return PRODUCT_ALIASES[token]
    for token in tokens:
        match = get_close_matches(token, PRODUCT_ALIASES.keys(), n=1, cutoff=0.78)
        if match:
            return PRODUCT_ALIASES[match[0]]
    return ""


def detect_rate_type(text):
    if is_per_kg_rate(text):
        return "per_kg"
    lower = str(text or "").lower()
    if re.search(r"\b(?:bhav|rate|ki|ka)\b", lower):
        return "per_unit"
    return "unknown"


def detect_payment_type(text):
    lower = str(text or "").lower()
    if re.search(r"\bcash|rokad|rokda|rupaye\s+(?:diye|diya)\b", lower):
        return "cash"
    if re.search(r"\budhar|khata|likho|jama|mila|mili|add\b", lower):
        return "ledger"
    return "unknown"


def score_parse_confidence(
    supplier_name,
    product_name,
    quantity,
    unit,
    rate,
    amount,
    ai_confidence=0,
    ai_uncertain_fields=None,
):
    uncertain = set(ai_uncertain_fields if isinstance(ai_uncertain_fields, list) else [])
    score = ai_confidence if 0 < ai_confidence <= 1 else 0.58
    if supplier_name:
        score += 0.08
    else:
        uncertain.add("supplier_name")
    if product_name:
        score += 0.08
    if quantity > 0:
        score += 0.08
    else:
        uncertain.add("quantity")
    if unit:
        score += 0.06
    if rate > 0:
        score += 0.08
    else:
        uncertain.add("rate")
    if amount > 0:
        score += 0.08
    else:
        uncertain.add("amount")
    return min(score, 0.98), sorted(uncertain)


def extract_weight_per_unit(text):
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:kg|kilo)\b", str(text or "").lower())
    return safe_float(match.group(1)) if match else 0


def is_per_kg_rate(text):
    lower = str(text or "").lower()
    return bool(re.search(r"\bper\s*(?:kg|kilo)\b|\b(?:kg|kilo)\s*(?:ka\s*)?bhav\b", lower))


def safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0


def normalize_spoken_numbers(text):
    for word, number in SPOKEN_NUMBERS.items():
        text = re.sub(rf"\b{word}\b", str(number), text)
    return text


def normalize_amount_words(text):
    multipliers = {
        "sau": 100,
        "sao": 100,
        "so": 100,
        "hundred": 100,
        "hazar": 1000,
        "hazaar": 1000,
        "hajaar": 1000,
        "thousand": 1000,
    }
    for word, multiplier in multipliers.items():
        text = re.sub(
            rf"\b(\d+(?:\.\d+)?)\s+{word}\b",
            lambda match: f"{safe_float(match.group(1)) * multiplier:g}",
            text,
        )
    return text


def split_joined_quantity_units(text):
    for number_word in sorted(SPOKEN_NUMBERS, key=len, reverse=True):
        for unit_word in sorted(UNIT_ALIASES, key=len, reverse=True):
            text = re.sub(rf"\b{number_word}{unit_word}\b", f"{number_word} {unit_word}", text)
    return text


def detect_transaction_type(text):
    lower = str(text or "").lower()
    if any(re.search(pattern, lower) for pattern in CREDIT_PATTERNS):
        return "credit"
    if any(re.search(pattern, lower) for pattern in DEBIT_PATTERNS):
        return "debit"
    return None
