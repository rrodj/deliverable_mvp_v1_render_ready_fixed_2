from flask import Blueprint, request, jsonify
from ..services.auth import require_auth
from ..services.db import get_session
from ..services.models import SalesRecord, MenuItem
import csv, io, datetime

bp = Blueprint("imports", __name__)

def _read_csv(file_storage):
    text = file_storage.read().decode("utf-8", errors="ignore")
    return list(csv.DictReader(io.StringIO(text)))

@bp.post("/sales")
@require_auth
def import_sales():
    f = request.files.get("file")
    if not f: return jsonify({"error":"file_required"}), 400
    rows = _read_csv(f); s = get_session(); cnt = 0
    for r in rows:
        try:
            d = datetime.date.fromisoformat((r.get("date") or "").strip())
            sku = (r.get("sku") or "").strip()
            if not sku: continue
            qty = int(float(r.get("qty") or 0)); price = float(r.get("unit_price") or 0.0); dr = float(r.get("discount_rate") or 0.0)
            s.add(SalesRecord(date=d, sku=sku, qty=qty, unit_price=price, discount_rate=dr)); cnt += 1
        except Exception: continue
    s.commit(); return jsonify({"rows_ingested": cnt}), 200

@bp.post("/onhand")
@require_auth
def import_onhand():
    f = request.files.get("file")
    if not f: return jsonify({"error":"file_required"}), 400
    rows = _read_csv(f); s = get_session(); cnt = 0
    for r in rows:
        sku = (r.get("sku") or "").strip()
        if not sku: continue
        on = int(float(r.get("on_hand") or r.get("onhand") or 0)); name = (r.get("name") or sku).strip(); price = float(r.get("price") or 0.0)
        it = s.query(MenuItem).filter_by(sku=sku).one_or_none()
        if not it: it = MenuItem(sku=sku, name=name, price=price, on_hand=on); s.add(it)
        else:
            it.on_hand = on
            if price: it.price = price
            if name: it.name = name
        cnt += 1
    s.commit(); return jsonify({"items_updated": cnt}), 200
