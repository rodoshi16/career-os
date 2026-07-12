# InternshipRadar

Monitors GitHub repos + company career pages + LinkedIn. Pings you instantly. One-click apply for Greenhouse/Lever. Auto-tracker. Mobile PWA.

---

## Setup (do this once, ~45 min total)

### Step 1 — Supabase (5 min)
1. Go to supabase.com → New project → pick a name
2. Once created: SQL Editor → paste the entire `supabase_schema.sql` → Run
3. Go to Settings → API → copy `Project URL` and `anon public` key

### Step 2 — VAPID keys for push notifications (2 min)
Go to https://vapidkeys.com → Generate → copy both keys

### Step 3 — Gmail App Password (3 min)
1. Google Account → Security → 2-Step Verification (enable if not on)
2. Search "App passwords" → create one called "InternshipRadar"
3. Copy the 16-char password

### Step 4 — Fill in your .env (5 min)
```bash
cd backend
cp .env.example .env
# Open .env and fill in every value
```

Also open `backend/services/apply.py` and fill in your personal info (name, email, school etc.) — used for auto-apply.

### Step 5 — Customize your watchlist (5 min)
Open `backend/services/config.py` and edit:
- `target_companies` — companies you want to monitor
- `greenhouse_companies` — find slug at `boards.greenhouse.io/{slug}`
- `lever_companies` — find slug at `jobs.lever.co/{slug}`
- `github_repos` — any job repos you want to watch

### Step 6 — Test locally (5 min)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Open http://localhost:8000 — you should see the app.

### Step 7 — Deploy to Railway (10 min)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
cd backend
railway init    # create new project
railway up      # deploy

# Add all your .env variables in Railway dashboard → Variables tab
# (copy each line from your .env file)
```
Copy your Railway URL (e.g. `https://radar-production.up.railway.app`)

### Step 8 — Install PWA on your iPhone (2 min)
1. Open your Railway URL in Safari on iPhone
2. Tap Share → "Add to Home Screen"
3. Go to Setup tab → tap "Enable Push Notifications"
4. Upload your resumes in the Resumes tab

Done. You'll get push notifications + emails the second anything drops.

---

## How to find ATS slugs

**Greenhouse:** Go to the company's jobs page. URL will be like `boards.greenhouse.io/apple` → slug is `apple`

**Lever:** Go to `jobs.lever.co/stripe` → slug is `stripe`

If a company uses Workday (Google, Microsoft, Amazon etc.) — the watcher can't auto-apply but you'll still get notified and can tap to open it.

---

## File structure
```
backend/
  main.py                      # FastAPI + scheduler
  watchers/
    github_watcher.py          # SimplifyJobs + GitHub repos
    careers_watcher.py         # Greenhouse + Lever APIs
    linkedin_watcher.py        # Your LinkedIn connections/follows
  services/
    config.py                  # YOUR WATCHLIST — edit this
    db.py                      # Supabase
    notify.py                  # Email + web push
    tailor.py                  # Claude resume tailoring
    apply.py                   # One-click apply (Greenhouse/Lever)
  api/
    routes.py                  # REST API for the PWA
  requirements.txt
  railway.toml

frontend/
  index.html                   # Full PWA (feed, tracker, resumes, settings)
  sw.js                        # Service worker (push + offline)
  manifest.json                # Makes it installable on iPhone

supabase_schema.sql            # Run once in Supabase SQL editor
```

## Cost
- Railway: $5/mo
- Anthropic: ~$1-2/mo (only when you use tailoring)
- Everything else: free
