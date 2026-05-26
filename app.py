from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

spec = spec_from_file_location("shop_supplier_ledger_backend", BACKEND_DIR / "app.py")
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load backend Flask app")

backend_app = module_from_spec(spec)
spec.loader.exec_module(backend_app)

app = backend_app.create_app()
