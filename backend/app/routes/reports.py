from flask import Blueprint, jsonify
from ..services.auth import require_auth
from ..services.db import get_session
from ..services.models import Evidence
from sqlalchemy import func
import datetime

bp = Blueprint("reports", __name__)

@bp.get("/roi")
@require_auth
def roi_summary():
    s = get_session()
    if s:
        mo = datetime.datetime.utcnow().strftime("%Y-%m")
        rows = s.query(Evidence.category, func.sum(Evidence.amount_usd)).filter(Evidence.month==mo, Evidence.status=="protected").group_by(Evidence.category).all()
        parts = {k: float(v or 0) for k, v in rows}
        total = round(sum(parts.values()), 2)
        return jsonify({
            "month": mo,
            "components": {
                "dead_stock": {"usd": parts.get("dead_stock", 0)},
                "stockouts": {"usd": parts.get("stockout_risk", 0)},
                "promo_bleed": {"usd": parts.get("promo_bleed", 0)},
                "alerts": {"usd": 0}
            },
            "total_protected_usd": total,
            "source": "evidence_db"
        }), 200
    # Fallback when DB disabled
    return jsonify({"month":"n/a","components":{"dead_stock":{"usd":100},"stockouts":{"usd":280},"promo_bleed":{"usd":360},"alerts":{"usd":0}},"total_protected_usd":740,"source":"seed"}), 200
