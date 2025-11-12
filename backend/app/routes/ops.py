from flask import Blueprint, jsonify
from ..services.auth import require_auth
from ..services import db as dbutil
from ..services.models import Base

bp = Blueprint("ops", __name__)

@bp.get("/db/status")
@require_auth
def db_status():
    eng = dbutil.get_engine()
    return jsonify({"db_enabled": bool(eng)}), 200

@bp.post("/db/init")
@require_auth
def db_init():
    eng = dbutil.get_engine()
    if not eng:
        return jsonify({"error":"db_not_configured"}), 400
    Base.metadata.create_all(eng)
    return jsonify({"ok": True, "message":"tables created (if not exist)"}), 200
