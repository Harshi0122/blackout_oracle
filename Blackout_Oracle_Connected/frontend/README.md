# Blackout Oracle frontend

This Vite app consumes the FastAPI backend in the sibling `../backend` directory.

For local development, requests to `/api/*` are proxied to `http://127.0.0.1:8000/*`. Start FastAPI first, then run:

```powershell
npm install
npm run dev
```

To point a built frontend to a separate API deployment, copy `.env.example` to `.env.production` and set `VITE_API_BASE_URL`.
