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

## Milestone 2 updates

### Environment validation
- Backend venv created, deps installed (fastapi, uvicorn, httpx, pydantic, pydantic-settings, pytest, pandas). `pytest -v`: 3 passed.
- Frontend deps installed, `tsc --noEmit` ok, `npm run build` ok (dist created).

### Verified API behavior (with evidence)
- FUELHH (actuals): `GET /datasets/FUELHH?format=json&publishDateTimeFrom=...&publishDateTimeTo=...` returns `{"data": [...]}`. Fields: `publishTime`, `startTime` (UTC Z), `fuelType`, `generation`, `settlementDate`, `settlementPeriod`. Half-hourly delivery intervals (`:00`, `:30`). For WIND in samples, often 1 publish per (startTime,fuelType) in the queried windows; revisions exist as per earlier samples.
- WINDFOR (forecasts): `GET /datasets/WINDFOR?format=json&publishDateTimeFrom=...&publishDateTimeTo=...` returns `{"data": [...]}`. Fields: `publishTime`, `startTime` (UTC Z), `generation`. Hourly delivery intervals (`:00` only) in samples. Multiple publishes per startTime (revisions) over time.
- Units: generation numeric (MW-scale in samples). Conversion not obvious from samples; treat as reported units, display consistently, document assumption.
- Retrieval: use publishDateTimeFrom/To filters; responses paginated by size (FUELHH returned 500 items for 12h window in sample). For full month need to chunk requests. No explicit pagination token seen in samples; may need to paginate by time windows.
- Duplicates/revisions: both have multiple publishTime per delivery interval; must select by publishTime <= cutoff and take latest eligible.

### Interval alignment comparison
Options:
1. **Align to hourly (WINDFOR grid)** - Use WINDFOR startTimes (:00). For each, find corresponding FUELHH WIND actual at same hour (if exists) and possibly aggregate half-hours? FUELHH has :00 and :30; averaging or summing depends on meaning (generation at settlement period) - risky without semantics. Pros: matches forecast resolution. Cons: loses half-hour actual detail, aggregation assumption.
2. **Align to half-hourly (FUELHH grid)** - Use FUELHH WIND startTimes (:00,:30). For each, look for WINDFOR forecast at same startTime - but WINDFOR has no :30 intervals in samples (only :00). Cannot directly match half-hour forecasts. Pros: keeps actual resolution. Cons: most intervals would have no WINDFOR forecast -> many exclusions.
3. **Align to hourly and only use FUELHH hours** - Drop FUELHH :30, evaluate only :00 intervals where both exist. Pros: clean 1:1. Cons: discards half the data, may not reflect full picture.

**Recommendation:** Option 3 (hourly alignment on :00 intervals where both datasets have records) is most defensible without inventing data. Must document exclusion rate and that half-hours are not evaluated. Do NOT interpolate/duplicate.

### Decision cutoff recommendation
- Challenge states "decisions made in January 2026" - do not equate to delivery dates. Delivery intervals may be for Jan but decision could be previous day.
- No explicit cutoff in provided docs. Day-ahead markets vary; common gate closures exist but not specified here. Treat 11:00 UTC as **configurable assumption only** (already in config). Must clearly label as assumption.
- Evaluation period: define as decisions made in Jan 2026 (by decision timestamp) mapped to relevant delivery intervals; need to be precise. Recommend making cutoff and decision window fully configurable and documenting assumptions.

### Remaining decisions requiring approval
- Approve interval alignment strategy (recommend hourly :00 only) and accept excluding half-hour intervals
- Confirm/adjust decision cutoff assumption (11:00 UTC) or provide official basis
- Confirm approach for full-month retrieval (time-chunking) given pagination

## Milestone 3 updates

### Implemented
- Enhanced Elexon client with chunking by publish time, error handling
- Normalization for FUELHH(WIND) and WINDFOR (UTC, separate publish/delivery)
- Pipeline for hourly alignment (:00 only), cutoff-based forecast selection, matching, exclusions tracking
- Metrics (MAE/RMSE/mean bias), error = forecast-actual
- API endpoints: /api/health, /api/overview, /api/accuracy, /api/forecast-history
- Tests added for hourly alignment, missing actuals, duplicate resolution

### Verified behavior
- Hourly :00 only; half-hour actuals counted as excluded (no interpolation/duplication)
- Forecasts must have publish_time <= cutoff; latest eligible selected
- Duplicates resolved deterministically (latest publish_time wins)
- Timezone-aware (UTC internally)

### API examples
- GET /api/health
- GET /api/overview?decision_date=2026-01-15&cutoff_hour_utc=11
- GET /api/accuracy?decision_date=2026-01-15
- GET /api/forecast-history?start_time=2026-01-15T12:00:00Z

### Unresolved assumptions
- Cutoff 11:00 UTC provisional (not official)
- Decision-date vs delivery-date mapping not fully specified; API takes decision_date but mapping logic needs refinement
- WINDFOR/FUELHH units assumed MW (reported) - verify if needed
- Full month retrieval may need larger chunking/pagination strategy

### Tests
- pytest: 6 passed
