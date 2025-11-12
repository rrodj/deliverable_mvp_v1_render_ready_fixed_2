# Combined Pilot‑Ready Patch

Generated: 2025-11-12T22:30:20Z

This single patch enables:
- **Postgres persistence** (data survives restarts)
- **Sales & On‑hand CSV imports**
- **Real rules** (stockout risk, dead stock, promo bleed)
- **Evidence ledger** (potential → protected)
- **ROI endpoints** (JSON + printable HTML)
- **Frontend Settings panel** for import & analysis

## Apply (repo root)
```bash
unzip -o combined_pilot_ready_patch.zip -d ./
cat backend/requirements.append.txt >> backend/requirements.txt
git add -A && git commit -m "Pilot-ready: DB + imports + rules + ROI + panel" && git push
```

## Render (backend service → Environment)
- `DATABASE_URL` = your Postgres URL
- `DB_AUTO_MIGRATE` = `1`
- Optional knobs:
  - `MARGIN_RATE=0.30`
  - `CARRYING_COST_RATE_MONTHLY=0.02`
  - `PLANNED_PROMO_RATE=0.10`
  - `STOCKOUT_DAYS_THRESHOLD=3`
Redeploy backend (and frontend, if your build copies the panel).

## Verify
1. `GET /ops/db/status` returns `{"db_enabled": true}`.
2. Upload **sales** and **on-hand** CSVs (Settings panel or endpoints below).
3. `POST /compute/scan` → findings and alerts created.
4. `GET /compute/evidence` → items listed.
5. `GET /reports/roi` and `/reports/roi/html` → totals and printable report.
