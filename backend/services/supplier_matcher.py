import re
from difflib import SequenceMatcher


MIN_MATCH_SCORE = 0.58


def normalize_name(value):
    text = str(value or "").casefold()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def supplier_match_score(spoken_text, supplier_name):
    spoken = normalize_name(spoken_text)
    supplier = normalize_name(supplier_name)
    if not spoken or not supplier:
        return 0

    if spoken == supplier:
        return 1

    spoken_tokens = spoken.split()
    supplier_tokens = supplier.split()

    if supplier in spoken:
        return 0.96
    if spoken in supplier and len(spoken) >= 2:
        return 0.9

    token_scores = [
        SequenceMatcher(None, spoken_token, supplier_token).ratio()
        for spoken_token in spoken_tokens
        for supplier_token in supplier_tokens
    ]
    best_token_score = max(token_scores) if token_scores else 0
    full_score = SequenceMatcher(None, spoken, supplier).ratio()

    return max(full_score, best_token_score)


def find_best_supplier_match(suppliers, parsed_supplier_name, voice_text):
    best_supplier = None
    best_score = 0
    search_values = [parsed_supplier_name, voice_text]

    for supplier in suppliers:
        supplier_name = supplier.get("supplier_name", "")
        score = max(supplier_match_score(value, supplier_name) for value in search_values)
        if score > best_score:
            best_supplier = supplier
            best_score = score

    if best_supplier and best_score >= MIN_MATCH_SCORE:
        return best_supplier, round(best_score, 2)

    return None, round(best_score, 2)
