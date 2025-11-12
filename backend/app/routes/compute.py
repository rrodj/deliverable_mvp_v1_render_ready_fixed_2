from flask import Blueprint, jsonify
from ..services.auth import require_auth
from ..services.rules import run_scan
from ..services.db import get_session
from ..services.models import Evidence
from sqlalchemy import desc

bp = Blueprint("compute", __name__)

@bp.post("/scan")
@require_auth
def scan():
    res = run_scan(); return jsonify(res), 200

@bp.get("/evidence")
@require_auth
def evidence():
    s = get_session()
    q = s.query(Evidence).order_by(desc(Evidence.created_at)).limit(200).all()
    out = [{
        "id": e.id, "month": e.month, "category": e.category, "status": e.status,
        "sku": e.sku, "item_name": e.item_name, "amount_usd": float(e.amount_usd or 0),
        "inputs": e.inputs, "created_at": e.created_at.isoformat()+"Z" if e.created_at else None
    } for e in q]
    return jsonify({"evidence": out}), 200
