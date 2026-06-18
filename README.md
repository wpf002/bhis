# BHIS — Biblical Health Intelligence System

A Scripture-anchored church diagnostic platform that measures what congregations actually believe, how they live it out, and where discipleship is breaking down.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 (async) + Alembic |
| Database | PostgreSQL 15 |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Auth | JWT (access + refresh tokens) |
| Cache | Redis |
| Infrastructure | Docker Compose |

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- Node.js 18+
- Python 3.11+

### 1. Clone and configure
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your values
```

### 2. Start everything with Docker
```bash
docker-compose up --build
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- FastAPI backend on http://localhost:8000
- React frontend on http://localhost:5173

### 3. Run migrations and seed data
```bash
docker-compose exec backend alembic upgrade head
docker-compose exec backend python seeds/seed_questions.py
```

### 4. Access the app
- **Frontend:** http://localhost:5173
- **API docs:** http://localhost:8000/docs
- **API redoc:** http://localhost:8000/redoc

---

## Development (without Docker)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Start Postgres locally and update .env
alembic upgrade head
python seeds/seed_questions.py
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
bhis/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings / environment
│   │   ├── database.py          # SQLAlchemy async engine
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── routers/             # API route handlers
│   │   ├── services/            # Business logic
│   │   │   ├── scoring_engine.py    # Core scoring algorithm
│   │   │   ├── drift_engine.py      # Drift detection
│   │   │   ├── archetype_engine.py  # Church archetype classification
│   │   │   └── recommendation_engine.py
│   │   ├── schemas/             # Pydantic request/response models
│   │   └── core/                # Auth, security, dependencies
│   ├── alembic/                 # Database migrations
│   ├── seeds/                   # Seed data (60 questions + options)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/               # Route-level components
│   │   ├── components/          # Reusable UI components
│   │   │   ├── dashboard/       # Dashboard-specific components
│   │   │   ├── survey/          # Survey-taking components
│   │   │   └── ui/              # Generic UI primitives
│   │   ├── services/            # API client
│   │   ├── hooks/               # Custom React hooks
│   │   └── types/               # TypeScript type definitions
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
└── docker-compose.yml
```

---

## User Roles

| Role | Access |
|---|---|
| `respondent` | Takes survey, views personal report |
| `leader` | Views church dashboard and aggregate data |
| `admin` | Manages church account, launches surveys |
| `consultant` | Read-only access to church dashboards (future) |

---

## Key Concepts

**Pillars** — 7 dimensions scored per respondent and aggregated at church level:
1. Doctrinal Integrity (20%)
2. Spiritual Discipline (15%)
3. Transformation & Fruit (20%)
4. Discipleship Depth (15%)
5. Church Health & Trust (12%)
6. Engagement & Alignment (10%)
7. Drift & Vulnerability (modifier: -8% to 0%)

**Maturity Tiers** — Disengaged / Nominal / Growing / Grounded / Multiplying Disciple

**Archetypes** — 12 church-level pattern classifications (e.g. "Orthodoxy Without Obedience", "Consumer Church")

**Contradiction Engine** — 7 question pairs that detect gaps between stated belief and reported behavior
# bhis
