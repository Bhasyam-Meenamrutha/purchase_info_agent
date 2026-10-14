"""Local dashboard API for purchase_info_agent. Run: python purchase_info_agent/dashboard.py"""
from pathlib import Path
import json, sqlite3, sys
from typing import Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = PROJECT_DIR / "purchase_info.db"
STATIC_DIR = PROJECT_DIR / "static"
try:
    from . import dummy_sap
except ImportError:
    sys.path.insert(0, str(PROJECT_DIR.parent))
    from purchase_info_agent import dummy_sap

app = FastAPI(title="Purchase Info Record Dashboard", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class RecordInput(BaseModel):
    supplier: str = Field(min_length=1, max_length=40)
    material: str = Field(min_length=1, max_length=40)
    purchasing_organization: str = Field(min_length=1, max_length=20)
    plant: str = Field(min_length=1, max_length=20)
    net_price: float = Field(gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    order_unit: str = Field(default="EA", min_length=1, max_length=10)
    planned_delivery_time: int = Field(default=7, ge=0, le=365)
    info_record_category: str = Field(default="Standard", min_length=1, max_length=30)

def connect():
    if not DB_PATH.exists():
        raise HTTPException(500, f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=10000")
    return conn

def row_record(row):
    result = dict(row)
    raw = result.pop("record_json", None)
    if raw:
        try:
            stored = json.loads(raw)
            stored.update({k:v for k,v in result.items() if v is not None})
            result = stored
        except (TypeError, json.JSONDecodeError):
            pass
    return result

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/health")
def health():
    with connect() as conn:
        conn.execute("SELECT 1")
    return {"status":"ok", "database":str(DB_PATH), "backend":"DUMMY_SAP"}

@app.get("/api/records")
def list_records(search: str = Query("", max_length=120),
                 status: str = Query("all", max_length=30),
                 category: str = Query("all", max_length=30)):
    try:
        with connect() as conn:
            rows = conn.execute("""SELECT info_record_number,supplier,material,
                purchasing_organization,plant,net_price,currency,order_unit,
                planned_delivery_time,info_record_category,created_at,record_json
                FROM purchase_info_records ORDER BY created_at DESC""").fetchall()
    except sqlite3.OperationalError as exc:
        raise HTTPException(500, f"Could not read purchase_info_records: {exc}")
    items = [row_record(r) for r in rows]
    if search.strip():
        q = search.strip().lower()
        items = [r for r in items if q in " ".join(str(r.get(k,"")) for k in
            ("info_record_number","supplier","material","purchasing_organization","plant")).lower()]
    if status != "all":
        items = [r for r in items if str(r.get("status","CREATED")).lower() == status.lower()]
    if category != "all":
        items = [r for r in items if str(r.get("info_record_category","Standard")).lower() == category.lower()]
    return {"items":items, "total":len(items), "backend":"DUMMY_SAP"}

@app.get("/api/records/{record_number}")
def get_record(record_number: str):
    with connect() as conn:
        row = conn.execute("""SELECT info_record_number,supplier,material,
            purchasing_organization,plant,net_price,currency,order_unit,
            planned_delivery_time,info_record_category,created_at,record_json
            FROM purchase_info_records WHERE info_record_number=?""",(record_number,)).fetchone()
    if not row:
        raise HTTPException(404, "Purchase Info Record not found")
    return row_record(row)

@app.post("/api/records", status_code=201)
def create_record(payload: RecordInput):
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    try:
        result = dummy_sap.create_dummy_purchase_info_record(data)
    except Exception as exc:
        raise HTTPException(500, f"Dummy backend failed: {exc}")
    if isinstance(result, dict):
        duplicate = bool(result.get("duplicate")) or str(result.get("status","")).upper() == "DUPLICATE"
        if duplicate or result.get("success") is False:
            raise HTTPException(409, result.get("message","Matching record already exists."))
        return {"message":"Dummy Purchase Info Record created.", "record":result.get("record",result), "backend":"DUMMY_SAP"}
    return {"message":"Dummy Purchase Info Record created.", "record":result, "backend":"DUMMY_SAP"}

@app.get("/api/meta")
def metadata():
    return {"backend":"DUMMY_SAP", "database":DB_PATH.name, "is_real_sap":False}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
