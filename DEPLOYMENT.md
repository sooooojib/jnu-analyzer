# JnU Analyzer — Production Deployment Guide

A comprehensive, zero-cost production deployment manual for **JnU Analyzer**. This guide enables any developer or DevOps engineer to clone a fresh repository and deploy the full stack with hardened security, automated migrations, ephemeral file cleanup, and health monitoring on permanently free and free-tier infrastructure.

---

## 1. Free-Tier vs. Open-Source vs. Future Scaling Cost Matrix

We prioritize open-source, self-hostable, and free-tier infrastructure. **Zero paid subscriptions are required to run this project.**

| Category | Component / Service | Tier / Model | Monthly Cost | Notes / Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **Permanently Free** | Python 3.12, Django 5, DRF | Open Source (MIT/BSD) | **$0.00** | Backend framework |
| **Permanently Free** | React 19, Vite, Tailwind CSS | Open Source (MIT) | **$0.00** | Frontend web application |
| **Permanently Free** | SQLite (Default Database) | Public Domain | **$0.00** | Stored locally in container/server |
| **Permanently Free** | WhiteNoise Static Files | Open Source (Apache-2.0) | **$0.00** | Fast Gzip/Brotli static assets |
| **Permanently Free** | Gunicorn WSGI Server | Open Source (MIT) | **$0.00** | Multi-threaded Python server |
| **Permanently Free** | Docker Engine & Multi-Stage Build | Open Source (Apache-2.0) | **$0.00** | Universal container packaging |
| **Permanently Free** | Google AI Studio (Gemini 2.0/1.5) | Free Web Interface | **$0.00** | Free vision AI prompt for result extraction |
| **Free-Tier Host** | **Render.com** (Web Service) | Free Tier (512MB RAM) | **$0.00** | 750 free compute hours/month (spins down after 15m inactivity) |
| **Free-Tier Host** | **Vercel / Netlify / Cloudflare** | Free Tier (CDN Edge) | **$0.00** | 100 GB/month bandwidth for React frontend |
| **Free-Tier Host** | **Neon / Supabase** (PostgreSQL) | Free Tier (500MB storage) | **$0.00** | Optional managed PostgreSQL database |
| **Future Cost** *(Optional)* | Render Starter Compute | Paid ($7 / month) | ~$7.00 | Keeps container awake 24/7 with zero spin-down latency |
| **Future Cost** *(Optional)* | Custom Domain Name | Registrar ($10 / year) | ~$0.83 | Optional custom branding (e.g. `analyzer.jnu.ac.bd`) |

---

## 2. Environment Variables Reference

Configure environment variables in your deployment platform's dashboard or via `.env`.

### Backend Environment Variables (`backend/.env`)

| Variable | Required | Default / Example | Description |
| :--- | :--- | :--- | :--- |
| `DEBUG` | **Yes** | `False` | Must be `False` in production for security. |
| `SECRET_KEY` | **Yes** | *[Random 50+ chars]* | Cryptographic signing key. System fails on boot if default/empty. |
| `DJANGO_SETTINGS_MODULE` | **Yes** | `config.settings.production` | Loads hardened production settings module. |
| `ALLOWED_HOSTS` | **Yes** | `jnu-analyzer.onrender.com,localhost` | Comma-separated domains allowed to serve traffic. |
| `CORS_ALLOWED_ORIGINS` | **Yes** | `https://jnu-analyzer.onrender.com` | Allowed browser origins for cross-origin API calls. |
| `CSRF_TRUSTED_ORIGINS` | **Yes** | `https://jnu-analyzer.onrender.com` | Trusted origins for CSRF security protection. |
| `SECURE_SSL_REDIRECT` | Optional | `True` | Automatically redirects all HTTP traffic to HTTPS. |
| `SESSION_COOKIE_SECURE` | Optional | `True` | Enforces `Secure` flag on session cookies (HTTPS only). |
| `CSRF_COOKIE_SECURE` | Optional | `True` | Enforces `Secure` flag on CSRF cookies (HTTPS only). |
| `SESSION_TTL_MINUTES` | Optional | `60` | Auto-expiry time in minutes for uploaded result sheets. |
| `MAX_UPLOAD_SIZE_MB` | Optional | `25` | Maximum upload size in megabytes. |
| `UPLOAD_DIR` | Optional | `/tmp/result_analyzer/uploads` | Ephemeral directory for temporary result sheet storage. |
| `DATABASE_URL` | Optional | `postgresql://...` | Optional PostgreSQL connection string. Defaults to SQLite if empty. |

### Frontend Environment Variables (`frontend/.env`)

| Variable | Required | Default / Example | Description |
| :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Optional | `/api/v1` | Base URL for API requests. Use `/api/v1` for single container, or full URL (e.g. `https://api.domain.com/api/v1`) for decoupled frontend. |

---

## 3. Production Architecture

JnU Analyzer supports two deployment patterns:

### Pattern A: Unified Single-Container (Recommended for Render / Fly.io / Railway / VPS)
```
[Browser / User]
       │ HTTPS (:443)
       ▼
[Cloud Load Balancer / Reverse Proxy (SSL Termination)]
       │ HTTP (:8000) (X-Forwarded-Proto: https)
       ▼
[Docker Container (Non-root 'appuser')]
   ├── Gunicorn WSGI Server (1 worker, 4 threads)
   ├── WhiteNoise Engine (serves /static/ and frontend /dist/ with Brotli/Gzip)
   ├── Django REST Framework API (/api/v1/...)
   ├── Health Check Probe (/api/health/)
   ├── Ephemeral Storage (/tmp/result_analyzer/uploads)
   └── SQLite Database (/app/backend/db.sqlite3)
```

### Pattern B: Decoupled Edge (Vercel Frontend + Render Backend)
- **Frontend**: Hosted on Vercel/Netlify with global CDN caching.
- **Backend**: Hosted on Render with `CORS_ALLOWED_ORIGINS` pointing to the Vercel domain.

---

## 4. Step-by-Step Deployment Instructions

### Option 1: One-Click / Git Deployment on Render (100% Free)

1. **Fork or Push Repository to GitHub**.
2. **Log into [Render.com](https://render.com)**.
3. Click **New +** -> **Blueprint**.
4. Select your GitHub repository containing `render.yaml`.
5. Render will automatically configure:
   - Environment: `Docker`
   - Plan: `Free`
   - Health Check Path: `/api/health/`
   - Automatic `SECRET_KEY` generation.
6. Click **Apply**.
7. Once built, access your live app at `https://<your-service-name>.onrender.com`.

---

### Option 2: Deploy to Fly.io (Free / Ultra-Low Cost)

1. Install Fly CLI: `brew install flyctl` or `curl -L https://fly.io/install.sh | sh`.
2. Login: `fly auth login`.
3. Launch app in workspace root:
   ```bash
   fly launch --no-deploy
   ```
4. Set production secrets:
   ```bash
   fly secrets set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))") \
                   DJANGO_SETTINGS_MODULE=config.settings.production \
                   ALLOWED_HOSTS=.fly.dev \
                   SECURE_SSL_REDIRECT=True
   ```
5. Deploy:
   ```bash
   fly deploy
   ```

---

### Option 3: Self-Hosted VPS (Ubuntu 22.04 / 24.04 with Docker + Nginx + Certbot)

1. **SSH into your VPS server**:
   ```bash
   ssh root@your-server-ip
   ```

2. **Install Docker and Nginx**:
   ```bash
   apt-get update && apt-get install -y docker.io docker-compose nginx certbot python3-certbot-nginx
   ```

3. **Clone Repository and Configure Environment**:
   ```bash
   git clone https://github.com/your-username/jnu-analyzer.git /opt/jnu-analyzer
   cd /opt/jnu-analyzer
   cp backend/.env.example backend/.env
   # Edit backend/.env and set your SECRET_KEY and domain in ALLOWED_HOSTS
   ```

4. **Build and Run Docker Container**:
   ```bash
   docker build -t jnu-analyzer:latest .
   docker run -d --name jnu-analyzer-app \
     --restart always \
     -p 127.0.0.1:8000:8000 \
     --env-file backend/.env \
     -v /var/run/result_analyzer:/tmp/result_analyzer \
     jnu-analyzer:latest
   ```

5. **Configure Nginx Reverse Proxy** (`/etc/nginx/sites-available/jnu-analyzer`):
   ```nginx
   server {
       server_name analyzer.yourdomain.com;

       client_max_body_size 30M;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

6. **Enable Site & Obtain Free SSL Certificate**:
   ```bash
   ln -s /etc/nginx/sites-available/jnu-analyzer /etc/nginx/sites-enabled/
   nginx -t && systemctl reload nginx
   certbot --nginx -d analyzer.yourdomain.com
   ```

7. **Set Up Scheduled Ephemeral File Cleanup**:
   Add a crontab job to purge sessions hourly:
   ```bash
   crontab -e
   # Add this line:
   0 * * * * docker exec jnu-analyzer-app python manage.py purge_expired_sessions >> /var/log/purge_sessions.log 2>&1
   ```

---

## 5. Security & Hardening Checklist

- [x] **No Hardcoded Secrets**: Secrets injected exclusively via environment variables.
- [x] **Secret Key Guard**: Production boots will halt immediately if `SECRET_KEY` is missing or default.
- [x] **Non-Root Container**: Docker container runs under dedicated unprivileged `appuser`.
- [x] **HTTPS Redirection**: Automatic `SECURE_SSL_REDIRECT` enabled for production.
- [x] **HSTS Header**: `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`.
- [x] **Secure Cookies**: `HttpOnly`, `SameSite=Lax`, and `Secure` enabled on all cookies.
- [x] **Clickjacking Protection**: `X-Frame-Options: DENY`.
- [x] **MIME Sniffing Protection**: `X-Content-Type-Options: nosniff`.
- [x] **Zero Persistent PII**: All uploads auto-expire via 60-minute TTL or manual session clear.
- [x] **Magic-Byte Binary Validation**: Uploads checked via magic bytes to prevent shell injection.
- [x] **Sanitized Audit Logging**: Student IDs and sensitive identifiers are redacted in server stdout logs.

---

## 6. Production Smoke-Test Checklist

Run this checklist immediately after deploying to verify operational readiness:

### 1. Health Probe
```bash
curl -i https://<your-domain>/api/health/
```
**Expected Response:** HTTP `200 OK` with JSON payload:
```json
{
  "status": "healthy",
  "service": "JnU Analyzer API",
  "version": "1.0.0",
  "uptime_seconds": 42,
  "checks": {
    "database": { "status": "healthy", "engine": "sqlite" },
    "ephemeral_storage": { "status": "healthy" }
  }
}
```

### 2. HTTPS & Security Headers Test
```bash
curl -I https://<your-domain>/
```
**Expected Headers:**
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`

### 3. UI Functionality Test
1. Visit `https://<your-domain>/` in browser.
2. Verify tab navigation (1. Upload -> 2. Verification -> 3. Dashboard -> 4. Analytics -> 5. Comparison).
3. Test Demo Mode: Click `"Try with Demo Data"` — verify all charts, histogram, scorecards, and comparisons render immediately without errors.
4. Test Vision AI Prompt: Click `"Extract with Vision AI"`, verify copy prompt button copies prompt to clipboard.
5. Test Session Expiry / Clear: Click the trash/clear button in navbar to verify immediate ephemeral purging.

### 4. Background Purge Command Test
```bash
# In local/container shell:
python manage.py purge_expired_sessions
```
**Expected Output:** `No expired sessions found. Ephemeral storage is clean.` (or count of deleted records).
