from flask import current_app, g
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, PyMongoError
from werkzeug.exceptions import ServiceUnavailable


def init_mongo(app):
    try:
        client = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=5000)
        db = client[app.config["MONGO_DB_NAME"]]

        suppliers = db[app.config["MONGO_SUPPLIERS_COLLECTION"]]
        transactions = db[app.config["MONGO_TRANSACTIONS_COLLECTION"]]

        suppliers.create_index("supplier_name")
        suppliers.create_index("mobile_number")
        transactions.create_index([("supplier_id", 1), ("date", 1), ("created_at", 1)])

        app.extensions["mongo_client"] = client
        app.extensions["mongo_db"] = db
    except (ConfigurationError, PyMongoError) as error:
        app.extensions["mongo_client"] = None
        app.extensions["mongo_db"] = None
        app.logger.warning("MongoDB startup skipped: %s", error)


def get_db():
    if "mongo_db" not in g:
        g.mongo_db = current_app.extensions["mongo_db"]
    if g.mongo_db is None:
        raise ServiceUnavailable("MongoDB is not configured or reachable")
    return g.mongo_db


def suppliers_collection(db=None):
    if db is None:
        db = get_db()
    return db[current_app.config["MONGO_SUPPLIERS_COLLECTION"]]


def transactions_collection(db=None):
    if db is None:
        db = get_db()
    return db[current_app.config["MONGO_TRANSACTIONS_COLLECTION"]]


def close_mongo(_error=None):
    g.pop("mongo_db", None)
