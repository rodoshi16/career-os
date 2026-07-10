import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from watchers.github_watcher import GitHubWatcher
from watchers.careers_watcher import CareersWatcher
from watchers.linkedin_watcher import LinkedInWatcher
from api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("main")

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🚀 InternshipRadar starting...")

    github  = GitHubWatcher()
    careers = CareersWatcher()
    linkedin = LinkedInWatcher()

    scheduler.add_job(github.check,   "interval", minutes=5,  id="github",   max_instances=1)
    scheduler.add_job(careers.check,  "interval", minutes=5,  id="careers",  max_instances=1)
    scheduler.add_job(linkedin.check, "interval", minutes=30, id="linkedin", max_instances=1)

    scheduler.start()

    # Run immediately on startup so you don't wait 5 min
    asyncio.create_task(github.check())
    asyncio.create_task(careers.check())

    log.info("✅ All watchers running")
    yield
    scheduler.shutdown()

app = FastAPI(title="InternshipRadar", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Serve the PWA frontend
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/health")
async def health():
    return {"status": "running", "jobs": [j.id for j in scheduler.get_jobs()]}

# Catch-all → serve PWA index.html (for client-side routing)
@app.get("/{full_path:path}")
async def serve_pwa(full_path: str):
    return FileResponse("../frontend/index.html")
