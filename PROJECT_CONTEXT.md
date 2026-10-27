# PROJECT_CONTEXT.md - Gridbricks WindSight

## Challenge summary
- Build WindSight: decision-time wind forecast vs actuals for UK national wind (Elexon)
- Scope: January 2026 decisions, national-level only
- Focus: forecast published <= decision cutoff for each delivery interval; avoid hindsight bias
- Metrics: MAE, RMSE, Mean Forecast Error/Bias (forecast - actual)
- Stack: React (TS/Vite/Tailwind/Recharts), Python (FastAPI/HTTPX/Pandas/Pydantic), Docker, deploy to Vercel/Heroku
- Deliverables: deployed app, public anonymous GitHub repo, README, unlisted YouTube <10min (5+5), submission form

## Current repo state
- Empty repo at /home/ansh/projects/job-app/gridbricks-challenge (no .git, no files)
- Need to scaffold fullstack app

## Verified Elexon API behavior (from live calls)
Base: https://data.elexon.co.uk/bmrs/api/v1
- FUELHH (actuals): `GET /datasets/FUELHH?format=json&publishDateTimeFrom=...&publishDateTimeTo=...` 
  - Fields seen: dataset, publishTime (UTC Z), startTime (UTC Z - delivery/start of half-hour), settlementDate, settlementPeriod, fuelType, generation
  - For WIND: multiple publishTime entries exist (revisions). Each record is a (publishTime, startTime, fuelType) snapshot.
  - Generation appears numeric (MW-like values seen ~13k+ for WIND)
- WINDFOR (forecasts): `GET /datasets/WINDFOR?format=json&publishDateTimeFrom=...&publishDateTimeTo=...`
  - Fields seen: dataset, publishTime (UTC Z), startTime (UTC Z - delivery interval), generation
  - Hourly resolution in samples (startTime hourly), publishTime gives forecast runs/revisions
  - Generation numeric

Both return arrays under `data` (based on sample). Times are UTC (Z). 30-min/settlement period structure exists in FUELHH; WINDFOR shows hourly in sampled data - need to confirm exact resolution and how it aligns.

## Key decisions/assumptions (to confirm)
- "Decisions made in January 2026" - need to define decision cutoff (e.g. day-ahead market). Not specified; must pick defensible configurable default and document.
- Must pick forecast with publishTime <= decision_cutoff for delivery interval (latest such forecast). No hindsight.
- Match by startTime (delivery). Normalize timezones (UK GMT in Jan, but be robust).
- Units: verify (looks like MW). Display consistently.
- Need to handle missing data, duplicates, revisions.

## Recommended first implementation
1. Scaffold monorepo: frontend/ (Vite+React+TS+Tailwind+Recharts), backend/ (FastAPI), docker-compose, .env.example
2. Build Elexon client with normalization for FUELHH(WIND) and WINDFOR
3. Implement forecast selection logic (by startTime, filter publishTime <= cutoff, take latest eligible)
4. Implement metrics (MAE/RMSE/bias) with tests
5. API endpoints /health, /overview, /accuracy, /forecast-history
6. Basic UI for overview + accuracy
7. Dockerize, test locally
8. Deploy, record video, submit

## Known risks
- WINDFOR resolution vs FUELHH settlement periods (need to align correctly)
- Defining decision cutoff without explicit rule - document assumption clearly
- API pagination/rate limits for full month
- Timezone handling

## Repository structure (Milestone 1)
```
gridbricks-challenge/
├── frontend/ (Vite+React+TS+Tailwind+Recharts)
├── backend/  (FastAPI+HTTPX+Pydantic+pytest)
├── docker-compose.yml
├── .env.example
├── README.md
└── PROJECT_CONTEXT.md
```

## Run commands
- Backend: `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm install && npm run dev`
- Tests: `cd backend && pytest -v`
- Docker: `docker compose up --build`

## Verified API facts (evidence)
- FUELHH: returns records with `publishTime`, `startTime` (UTC Z), `fuelType`, `generation`, `settlementDate`, `settlementPeriod`. Multiple publishes per (startTime,fuelType). WIND present.
- WINDFOR: returns `publishTime`, `startTime` (UTC Z), `generation`. Hourly in samples; multiple publishes per interval. Generation numeric.
- Both under base `https://data.elexon.co.uk/bmrs/api/v1/datasets/{DATASET}` with `format=json` and date filters observed; response shape `{"data": [...]}` in samples.

## Normalization contract (proposed)
- Actuals (FUELHH, WIND): delivery_start = startTime (UTC), publish_time = publishTime (UTC), generation, fuel_type, source, settlement metadata
- Forecasts (WINDFOR): delivery_start = startTime (UTC), publish_time = publishTime (UTC), generation, source
- Keep UTC internally; convert to UK local for display. No interpolation/resampling without review.

## Decision-time methodology
- Scope: decisions made in January 2026 (delivery intervals may span; need careful mapping). Not assuming delivery==decision month.
- Cutoff: configurable (env `DECISION_CUTOFF_HOUR_UTC`, default 11 UTC) - provisional assumption, not official rule. Documented.
- Rule: select latest forecast with publish_time <= decision_cutoff for that delivery interval (prevents hindsight bias).

## Unresolved questions / impact
- WINDFOR temporal resolution vs FUELHH half-hourly - alignment unclear; cannot resample blindly.
- Exact official day-ahead cutoff - research needed; using configurable default for now.
- Pagination/size limits for full Jan 2026 - need to verify retrieval strategy.
- Completeness vs truncation - must detect and surface.

## Milestone 1 status
- Scaffold created, tests added for selection/metrics, normalization schemas defined.
- API verification done via live calls; details documented.
- Next: confirm resolution/alignment + cutoff approach before full analytics/UI.
