# Blackout Oracle Backend API Analysis

## Backend selected for integration

The uploaded `backend.zip` contains more than one backend/frontend tree. The integration in this frontend uses:

`backend/Blackout_Oracle/backend/app/main.py`

This is the backend with the modular FastAPI route set and the `backend/Blackout_Oracle/Makefile`.

## Startup

From `backend/Blackout_Oracle`:

```bash
make run
```

The Makefile starts:

```bash
cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Default API base URL: `http://localhost:8000`

CORS is configured in `app/main.py` with `allow_origins=["*"]` and no credentials.

## System routes

- `GET /`
- `GET /health`
- `GET /ready`
- `GET /version`
- `GET /health/live`

## Assets

- `GET /assets`
- `GET /assets/{id}`
- `GET /assets/{id}/status`
- `GET /assets/{id}/telemetry`
- `GET /assets/summary/counts`

Mutation routes also exist for internal asset management but are not automatically invoked by the frontend.

## Telemetry

- `GET /telemetry`
- `GET /telemetry/latest/{asset_id}`
- `GET /telemetry/health`
- `GET /telemetry/summary`

## Weather

- `GET /weather/latest?latitude={latitude}&longitude={longitude}`
- `GET /weather/observations`
- `GET /weather/forecasts`
- `GET /weather/health`
- `GET /weather/risk`
- `GET /weather/summary`

`/weather/latest` requires latitude and longitude. The frontend now supplies them dynamically through user selection, browser geolocation after explicit interaction, or a clearly labelled demo default.

## Risk

- `GET /risk/latest`
- `GET /risk/assessments/{id}`
- `GET /risk/history`
- `GET /risk/factors`
- `GET /risk/summary`
- `POST /risk/assess`

The request schema for `POST /risk/assess` is `RiskAssessmentRequest`.

## Alerts

- `GET /alerts`
- `GET /alerts/{id}`
- `GET /alerts/summary/counts`
- `POST /alerts/{id}/acknowledge` with `AlertAcknowledgeRequest`
- `POST /alerts/{id}/resolve` with `AlertResolveRequest`
- `POST /alerts/{id}/dismiss`

Alert mutation requests are explicit user actions only.

## Incidents

- `GET /incidents`
- `GET /incidents/{id}`
- `GET /incidents/{id}/status`
- `GET /incidents/{id}/timeline`
- `GET /incidents/summary/counts`
- `POST /incidents/{id}/resolve` with `IncidentResolveRequest`
- `POST /incidents/{id}/false-positive`

## Simulations

- `POST /simulations`
- `POST /simulations/{id}/run`
- `GET /simulations/{id}`
- `GET /simulations/{id}/result`
- `POST /simulations/{id}/cancel`

The frontend uses the actual create → run → status polling → result workflow. Polling only continues for `queued` and `running` states.

## Recommendations

- `GET /recommendations`
- `GET /recommendations/{id}`
- `GET /recommendations/{id}/status`
- `POST /recommendations/{id}/approve` with `RecommendationReviewRequest`
- `POST /recommendations/{id}/reject` with `RecommendationReviewRequest`
- `POST /recommendations/{id}/executed` with `RecommendationReviewRequest`

No permanent `operator-1` identity is hardcoded. Since this backend does not expose an authentication/session identity mechanism, the frontend exposes a clearly labelled development operator identity input.

## Important runtime behavior

The modular backend currently uses in-memory development stores for several domains. If those stores have not been seeded or populated, endpoints can legitimately return empty data or `404` for “latest” resources. The frontend therefore shows an unavailable/partial state and does not replace failed backend responses with mock dashboard data.
