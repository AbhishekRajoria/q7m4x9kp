# Gridbricks WindSight (Work in Progress)

Energy analytics dashboard for UK national wind generation: compare decision-time forecasts (Elexon WINDFOR) with actuals (Elexon FUELHH) for January 2026 procurement decisions.

## Status
Milestone 1 - scaffolding and data-contract verification in progress. Core analytics not yet implemented.

## Tech Stack
- Frontend: React + TypeScript + Vite + Tailwind CSS + Recharts
- Backend: Python + FastAPI + HTTPX + Pydantic + pytest
- Infra: Docker Compose (local dev)

## Quick Start (local)
### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker Compose
```bash
docker compose up --build
```

## Environment
Copy `.env.example` to `.env` and adjust as needed.

## Data Sources
- FUELHH (actuals): https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH
- WINDFOR (forecasts): https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR

## Notes
- AI tools used: disclosed in final README (to be added)
- Deployment URL: TBD
- Video: TBD
