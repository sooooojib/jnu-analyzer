# JnU Analyzer

**JnU Analyzer** is a privacy-first academic result tabulation and analytics platform. It performs deterministic extraction, cohort statistical analysis, GPA/CGPA distribution calculations, current vs. cumulative academic tracking, and dual-student head-to-head comparisons from uploaded result sheets.

---

## Key Highlights

- **Privacy-First & Ephemeral**: Zero permanent user accounts; automatic 60-minute TTL purge routine.
- **Deterministic Analytics Engine**: Credit-weighted arithmetic GPA calculations, dense & competition ranking, standard deviation, mean, median, mode, and subject-wise leaderboards.
- **Vision AI Prompt Studio**: Free universal Markdown extraction prompt compatible with Google AI Studio (Gemini 2.0/1.5 Pro), Claude, and ChatGPT.
- **100% Free-Tier & Open Source**: Built with Django 5, React 19, Tailwind CSS, WhiteNoise, and SQLite/PostgreSQL with zero required paid services.

---

## Quick Start for Local Development

### 1. Prerequisites

- **Python**: `3.11+` (tested on Python 3.12 & 3.13)
- **Node.js**: `v18+` or `v20+` (tested on Node v22)
- **Git**

### 2. Clone & Setup Backend

```bash
# 1. Clone the repository
git clone https://github.com/your-username/jnu-analyzer.git
cd jnu-analyzer/backend

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install backend dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create environment file
cp .env.example .env

# 5. Run database migrations
python manage.py migrate

# 6. Start backend development server
python manage.py runserver 127.0.0.1:8000
```
API is live at `http://127.0.0.1:8000/api/v1/`  
Health check endpoint: `http://127.0.0.1:8000/api/health/`

### 3. Setup Frontend

```bash
# Open a second terminal window
cd jnu-analyzer/frontend

# 1. Install frontend dependencies
npm install

# 2. Create environment file
cp .env.example .env

# 3. Start frontend development server
npm run dev
```
Interactive UI is live at `http://localhost:5173/`

---

## Running Automated Tests

### Backend Tests
```bash
cd backend
source venv/bin/activate
python manage.py test tests
```

### Frontend Tests & Production Build Check
```bash
cd frontend
npm test -- --run
npm run build
```

---

## Production Deployment

For complete, step-by-step production deployment instructions (including Render, Fly.io, Vercel, Docker, and self-hosted VPS), see the **[Production Deployment Guide (DEPLOYMENT.md)](./DEPLOYMENT.md)**.

### Quick Docker Deployment (Single Container)
```bash
# Build production multi-stage container
docker build -t jnu-analyzer:latest .

# Run container locally or on any cloud host
docker run -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e DJANGO_SETTINGS_MODULE="config.settings.production" \
  -e ALLOWED_HOSTS="localhost,127.0.0.1" \
  jnu-analyzer:latest
```

---

## Core API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health/` | Active DB & storage health check probe |
| `POST` | `/api/v1/upload/` | Upload result sheet and create ephemeral session |
| `GET` | `/api/v1/sessions/{id}/status/` | Inspect status of an active session |
| `DELETE` | `/api/v1/sessions/{id}/` | Explicitly purge uploaded files and dataset |
| `POST` | `/api/v1/sessions/{id}/process/` | Parse and compute complete analytical dataset |
| `GET` | `/api/v1/sessions/{id}/dataset/` | Fetch normalized student & course table data |
| `GET` | `/api/v1/sessions/{id}/students/{student_id}/` | Retrieve individual student academic scorecard |
| `GET` | `/api/v1/sessions/{id}/analytics/` | Retrieve cohort summary, mean, median, distributions |
| `GET` | `/api/v1/sessions/{id}/compare/?student_a={A}&student_b={B}` | Head-to-head student comparative breakdown |

---

## Maintenance & Periodic Cleanup

To manually purge expired sessions from disk and database:
```bash
cd backend
source venv/bin/activate
python manage.py purge_expired_sessions
```
*(Note: Sessions are also purged automatically every 50 API requests and upon reaching their 60-minute TTL).*
