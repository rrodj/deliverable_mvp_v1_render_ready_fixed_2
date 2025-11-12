from datetime import date, datetime, timedelta
from typing import Dict, Any
from sqlalchemy import func
from ..services.db import get_session
from ..services.models import MenuItem, SalesRecord, Evidence, Alert
from flask import current_app

def _cfg(name, default):
    v = current_app.config.get(name)
    if v is None: return default
    try:
        if isinstance(default, float): return float(v)
        if isinstance(default, int): return int(v)
    except Exception: pass
    return v

def avg_daily_velocity(window_days:int=30):
    s = get_session()
    if not s: return {}
    since = date.today() - timedelta(days=window_days)
    rows = s.query(SalesRecord.sku, func.sum(SalesRecord.qty)).filter(SalesRecord.date >= since).group_by(SalesRecord.sku).all()
    return {sku: (qty or 0)/max(1, window_days) for sku, qty in rows}

def run_scan() -> Dict[str, Any]:
    s = get_session()
    if not s: return {"error":"db_disabled"}

    margin_rate = _cfg("MARGIN_RATE", 0.30)
    carrying_rate = _cfg("CARRYING_COST_RATE_MONTHLY", 0.02)
    planned_disc = _cfg("PLANNED_PROMO_RATE", 0.10)
    stockout_days = _cfg("STOCKOUT_DAYS_THRESHOLD", 3)

    month = datetime.utcnow().strftime("%Y-%m")
    s.query(Evidence).filter(Evidence.month==month, Evidence.status=="potential").delete()

    vel = avg_daily_velocity(30)
    items = {m.sku: m for m in s.query(MenuItem).all()}

    potential_total = 0.0
    created_alerts = 0

    # Dead stock
    since60 = date.today() - timedelta(days=60)
    sold_recent = set(x[0] for x in s.query(SalesRecord.sku).filter(SalesRecord.date >= since60).distinct().all())
    for sku, it in items.items():
        if sku not in sold_recent and (it.on_hand or 0) > 0:
            amt = float(it.on_hand or 0) * float(it.price or 0) * carrying_rate
            s.add(Evidence(month=month, category="dead_stock", status="potential", sku=sku, item_name=it.name, amount_usd=amt,
                           inputs={"on_hand": int(it.on_hand or 0), "unit_price": float(it.price or 0), "carrying_rate": carrying_rate}))
            potential_total += float(amt or 0)

    # Stockout risk
    for sku, v in vel.items():
        it = items.get(sku)
        if not it or v <= 0: continue
        on = int(it.on_hand or 0)
        if on <= 0: continue
        days_to_zero = on / v
        if days_to_zero <= stockout_days:
            lost_units = max(0.0, stockout_days * v - on)
            amt = float(it.price or 0) * margin_rate * lost_units
            s.add(Evidence(month=month, category="stockout_risk", status="potential", sku=sku, item_name=it.name, amount_usd=amt,
                           inputs={"velocity_per_day": v, "on_hand": on, "unit_price": float(it.price or 0), "margin_rate": margin_rate, "days_to_zero": days_to_zero, "threshold": stockout_days}))
            s.add(Alert(type="stockout_risk", level="warning", message=f"{sku} may stockout in {days_to_zero:.1f} days", sku=sku)); created_alerts += 1
            potential_total += float(amt or 0)

    # Promo bleed
    since30 = date.today() - timedelta(days=30)
    rows = s.query(SalesRecord.sku, func.sum(SalesRecord.qty*SalesRecord.unit_price), func.avg(SalesRecord.discount_rate)).filter(SalesRecord.date >= since30).group_by(SalesRecord.sku).all()
    for sku, gross, avgdisc in rows:
        gross = float(gross or 0.0); avgdisc = float(avgdisc or 0.0)
        extra = max(0.0, avgdisc - planned_disc)
        if gross > 0 and extra > 0:
            amt = gross * extra * 0.5  # 50% recoverable
            name = items.get(sku).name if items.get(sku) else None
            s.add(Evidence(month=month, category="promo_bleed", status="potential", sku=sku, item_name=name, amount_usd=amt,
                           inputs={"gross": gross, "avg_discount": avgdisc, "planned": planned_disc, "excess": extra, "intervention_fraction": 0.5}))
            potential_total += float(amt or 0)

    s.commit()
    return {"created_alerts": created_alerts, "potential_usd": round(potential_total, 2)}
