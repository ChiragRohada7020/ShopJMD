from flask import current_app, g
from pymongo import MongoClient


def init_mongo(app):
    client = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=5000)
    db = client[app.config["MONGO_DB_NAME"]]
    app.extensions["mongo_client"] = client
    app.extensions["mongo_db"] = db

    db.suppliers.create_index("supplier_name")
    db.suppliers.create_index("mobile_number")
    db.transactions.create_index([("supplier_id", 1), ("date", 1), ("created_at", 1)])


def get_db():
    if "mongo_db" not in g:
        g.mongo_db = current_app.extensions["mongo_db"]
    return g.mongo_db


def close_mongo(_error=None):
    g.pop("mongo_db", None)
