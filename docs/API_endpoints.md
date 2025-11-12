# Endpoints (added by this patch)

- `GET /ops/db/status` — DB on/off
- `POST /ops/db/init` — create tables (idempotent)
- `POST /imports/sales` — CSV: date,sku,qty,unit_price,discount_rate
- `POST /imports/onhand` — CSV: sku,on_hand[,name,price]
- `POST /compute/scan` — run rules (writes Evidence + stockout Alerts)
- `GET /compute/evidence` — latest Evidence rows
- `GET /reports/roi` — totals from protected Evidence (fallback to seed if DB off)
- `GET /reports/roi/html` — printable ROI
