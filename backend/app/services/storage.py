import uuid, datetime, os
from flask import current_app
from . import db as dbutil
from .models import MenuItem, Calibration, Alert, BillingEvent, BillingState, RoiSnapshot, SalesRecord

# In-memory fallback when DATABASE_URL is not set
MEM = { "menus": [], "calibrations": [], "alerts": [], "billing": {}, "billing_events": [] }

def _use_db():
    return bool(current_app.config.get("DATABASE_URL") or os.getenv("DATABASE_URL"))

def _menuitem_to_dict(m: MenuItem):
    return {"id": m.id, "sku": m.sku, "name": m.name, "price": float(m.price or 0), "on_hand": int(m.on_hand or 0),
            "created_at": (m.created_at.isoformat()+"Z") if m.created_at else None}

def _cal_to_dict(c: Calibration):
    return {"id": c.id, "device_id": c.device_id, "offset": float(c.offset or 0), "note": c.note,
            "timestamp": (c.created_at.isoformat()+"Z") if c.created_at else None}

def _alert_to_dict(a: Alert):
    return {"id": a.id, "type": a.type, "message": a.message, "level": a.level, "sku": a.sku,
            "timestamp": (a.created_at.isoformat()+"Z") if a.created_at else None}

# Menus
def add_menu_items(items):
    if _use_db():
        s = dbutil.get_session()
        for it in items or []:
            sku = (it.get("sku") or "").strip()
            if not sku: continue
            row = s.query(MenuItem).filter_by(sku=sku).one_or_none()
            if row is None:
                row = MenuItem(sku=sku, name=it.get("name") or sku, price=it.get("price") or 0, on_hand=it.get("on_hand") or 0)
                s.add(row)
            else:
                row.name = it.get("name") or row.name
                if it.get("price") is not None: row.price = it.get("price")
                if it.get("on_hand") is not None: row.on_hand = it.get("on_hand")
        s.commit()
    else:
        MEM["menus"].extend(items or [])

def list_menu_items():
    if _use_db():
        s = dbutil.get_session()
        return [_menuitem_to_dict(m) for m in s.query(MenuItem).order_by(MenuItem.created_at.desc()).all()]
    return MEM["menus"]

# Calibrations
def add_calibration(device_id, offset, note=None):
    if _use_db():
        s = dbutil.get_session(); c = Calibration(device_id=device_id, offset=float(offset or 0), note=note)
        s.add(c); s.commit(); s.refresh(c); return _cal_to_dict(c)
    c = {"id": str(uuid.uuid4()), "device_id": device_id, "offset": float(offset), "note": note,
         "timestamp": datetime.datetime.utcnow().isoformat()+"Z"}
    MEM["calibrations"].append(c); return c

def list_calibrations():
    if _use_db():
        s = dbutil.get_session()
        return [_cal_to_dict(c) for c in s.query(Calibration).order_by(Calibration.created_at.desc()).all()]
    return MEM["calibrations"]

# Alerts
def add_alert(alert_type, message, level="info", sku=None):
    if _use_db():
        s = dbutil.get_session(); a = Alert(type=alert_type, message=message, level=level, sku=sku)
        s.add(a); s.commit(); s.refresh(a); return _alert_to_dict(a)
    a = {"id": str(uuid.uuid4()), "type": alert_type, "message": message, "level": level, "sku": sku,
         "timestamp": datetime.datetime.utcnow().isoformat()+"Z"}
    MEM["alerts"].append(a); return a

def list_alerts():
    if _use_db():
        s = dbutil.get_session()
        return [_alert_to_dict(a) for a in s.query(Alert).order_by(Alert.created_at.desc()).all()]
    return MEM["alerts"]

# Billing
def add_billing_event(evt):
    if _use_db():
        s = dbutil.get_session(); be = BillingEvent(type=evt.get("type",""), ts=int(evt.get("ts") or 0), payload=evt)
        s.add(be); s.commit()
    else:
        buf = MEM.setdefault("billing_events", []); buf.append(evt); 
        if len(buf) > 50: del buf[:-50]

def list_billing_events():
    if _use_db():
        s = dbutil.get_session(); rows = s.query(BillingEvent).order_by(BillingEvent.id.desc()).limit(50).all()
        return [{"id": r.id, "type": r.type, "ts": r.ts, "payload": r.payload} for r in rows]
    return list(MEM.get("billing_events", []))

def get_billing_state():
    if _use_db():
        s = dbutil.get_session(); row = s.query(BillingState).get(1)
        return (row.state if row else {})
    return dict(MEM.get("billing", {}))

def set_billing_state(update):
    if _use_db():
        s = dbutil.get_session(); row = s.query(BillingState).get(1)
        if not row: row = BillingState(id=1, state={}); s.add(row); s.flush()
        cur = row.state or {}; cur.update({k:v for k,v in (update or {}).items() if v is not None})
        row.state = cur; s.commit(); return cur
    cur = MEM.setdefault("billing", {}); cur.update({k:v for k,v in (update or {}).items() if v is not None}); return cur

# Sales & ROI snapshots
def add_sales_rows(rows):
    if not _use_db(): return 0
    s = dbutil.get_session(); from datetime import datetime as _dt
    cnt = 0
    for r in rows or []:
        try:
            dt = r["date"]; 
            if isinstance(dt, str): dt = _dt.fromisoformat(dt).date()
            rec = SalesRecord(date=dt, sku=r["sku"], qty=int(r.get("qty") or 0),
                              unit_price=float(r.get("unit_price") or 0.0), discount_rate=float(r.get("discount_rate") or 0.0))
            s.add(rec); cnt += 1
        except Exception: continue
    s.commit(); return cnt

def save_roi_snapshot(month: str, total: float, components: dict):
    if not _use_db(): return
    s = dbutil.get_session(); snap = RoiSnapshot(month=month, total_protected_usd=float(total or 0), components=components or {})
    s.add(snap); s.commit()
