from datetime import date, datetime

from bson import ObjectId


def is_object_id(value):
    return ObjectId.is_valid(str(value))


def to_float(value, default=0):
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_date_string(value=None):
    if not value:
        return date.today().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise ValueError("Date must use YYYY-MM-DD format") from exc
