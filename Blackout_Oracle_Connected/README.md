# Blackout Oracle — connected frontend and backend

The React dashboard calls the FastAPI service through `/api`. During local development, Vite proxies `/api/*` to `http://127.0.0.1:8000/*`; no browser CORS setup is needed.

## Run locally

Open two terminals from this folder.

```powershell
cd backend
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm install
npm run dev
```

Open the address printed by Vite (usually `http://localhost:5173`). The status badge should show `LIVE • API` once FastAPI is available.

## Deployment configuration

For a separately hosted API, copy `frontend/.env.example` to `frontend/.env.production` and set `VITE_API_BASE_URL` to the API's public address. Keep the backend CORS allow-list restricted to the frontend origin in production.

## Notes

- The backend uses development-only in-memory stores; its data resets on restart.
- Recommendation review buttons and the Digital Twin simulation runner call the FastAPI endpoints directly.
