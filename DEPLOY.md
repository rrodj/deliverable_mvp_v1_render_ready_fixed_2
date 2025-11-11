# Deploy to Render — Inventory Guardian

This repo is **Render-ready**. You can deploy either **manually** (two services) or via a **Blueprint** (one `render.yaml`). Both paths are documented below.

---

## 1) Manual deploy (two services)

### Backend (Web Service)
- **Root Directory**: `backend`
- **Environment**: `Python`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `bash scripts/render-start.sh`
- **Health Check Path**: `/healthz`
- **Plan**: `Starter`
- **Environment Variables**:
  - `PYTHON_VERSION=3.11`
  - `APP_ENV=production`
  - `SECRET_KEY` – set a strong value
  - (optional) `CORS_ORIGINS`, `DEMO_API_TOKEN`, Stripe variables below

> After creating the backend service, click **Manual Deploy → Clear build cache & deploy**.

### Frontend (Static web on Render)
- **Type**: `Web`
- **Runtime**: `Static`
- **Root Directory**: `.`
- **Build Command**: `npm ci && npm run build`
- **Publish Directory**: `frontend/dist`
- **Environment Variables**:
  - `VITE_API_BASE_URL` ← **Add** → **From Service**:
    - **Name**: `inventory-guardian-backend`
    - **Type**: `web`
    - **envVarKey**: `RENDER_EXTERNAL_URL`

> After creating the frontend service, click **Manual Deploy → Clear build cache & deploy**.

**Validation checks**
- Backend logs should include `Listening at: http://0.0.0.0:$PORT` from Gunicorn.
- `GET /healthz` returns `200`.

---

## 2) Blueprint deploy (recommended)

1. Push this repo to your GitHub (or GitLab/Bitbucket) **empty** repo (see “GitHub one‑liner” below).
2. In Render:
   - **New → Blueprint** and pick the repo.
   - The Blueprint will detect two services from `render.yaml`:
     - **inventory-guardian-backend** (web, python)
     - **inventory-guardian-frontend** (web, static)
3. In the **backend** service → **Environment** tab, set:
   - `SECRET_KEY` (Render will prompt since it’s `sync: false`)
   - Optional: `CORS_ORIGINS`, `DEMO_API_TOKEN`, Stripe vars.
4. Click **Apply**.
5. In each service → **Manual Deploy** → **Clear build cache & deploy** (deploy **backend first**, then **frontend**).

> If you previously saw Blueprint errors like `unknown type static`, `invalid service property: url`, or `no such plan starter for service type web`, this repo fixes them by using `type: web` with `runtime: static`, wiring the API base URL via `fromService.envVarKey: RENDER_EXTERNAL_URL`, and removing `plan` from the static service.

---

## 3) Local smoke test

```bash
# From repo root
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Run exactly like Render
bash backend/scripts/render-start.sh &
sleep 2
curl -i http://127.0.0.1:8000/healthz
```

You should see `HTTP/1.1 200 OK`.

---

## 4) Environment variables

An example file is provided at [`config/env.example`](config/env.example). Copy values into Render as needed.

- `APP_ENV` (default `production`)
- `APP_VERSION` (default `0.1.0-mvp`)
- `SECRET_KEY` (**required in production**)
- `CORS_ORIGINS` (default `*`)
- `DEMO_API_TOKEN` (optional demo auth)
- **Stripe (optional)**: `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_STARTER`, `STRIPE_PRICE_PRO`, `STRIPE_PRICE_ENTERPRISE`, `STRIPE_BILLING_PORTAL_URL`
- Frontend build‑time: `VITE_API_BASE_URL` (wired from backend via Blueprint)

---

## 5) Notes

- The backend starts with a robust launcher that **doesn’t rely on PATH**:
  `exec "$PY" -m gunicorn wsgi:app --workers 2 --threads 8 --bind 0.0.0.0:${PORT:-8000}`
- Health endpoint is **`/healthz`** and returns 200.
- Python version is pinned via `PYTHON_VERSION=3.11` in the Blueprint.
