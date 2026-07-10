import logging
from supabase import create_client, Client
from services.config import settings

log = logging.getLogger("db")
_client: Client = None

def get_db() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client

# ── Deduplication ─────────────────────────────────────────────────────────────

async def is_seen(job_id: str) -> bool:
    res = get_db().table("seen_jobs").select("job_id").eq("job_id", job_id).execute()
    return len(res.data) > 0

async def mark_seen(job_id: str, job: dict):
    get_db().table("seen_jobs").insert({
        "job_id": job_id,
        "company": job.get("company"),
        "role": job.get("role"),
        "source": job.get("source"),
        "url": job.get("url"),
    }).execute()

# ── Resumes ───────────────────────────────────────────────────────────────────

async def save_resume(name: str, content: str) -> str:
    res = get_db().table("resumes").upsert({
        "name": name,
        "content": content,
    }, on_conflict="name").execute()
    return res.data[0]["id"]

async def get_resumes() -> list[dict]:
    res = get_db().table("resumes").select("*").order("created_at").execute()
    return res.data

async def get_resume(resume_id: str) -> dict | None:
    res = get_db().table("resumes").select("*").eq("id", resume_id).execute()
    return res.data[0] if res.data else None

async def delete_resume(resume_id: str):
    get_db().table("resumes").delete().eq("id", resume_id).execute()

# ── Push subscriptions ────────────────────────────────────────────────────────

async def save_push_subscription(sub: dict):
    get_db().table("push_subscriptions").upsert({
        "endpoint": sub["endpoint"],
        "subscription": sub,
    }, on_conflict="endpoint").execute()

async def get_push_subscriptions() -> list[dict]:
    res = get_db().table("push_subscriptions").select("subscription").execute()
    return [row["subscription"] for row in res.data]

# ── Applications ──────────────────────────────────────────────────────────────

async def log_application(job: dict, resume_id: str = None) -> dict:
    res = get_db().table("applications").insert({
        "company": job.get("company"),
        "role": job.get("role"),
        "url": job.get("url"),
        "source": job.get("source"),
        "ats": job.get("ats"),
        "resume_id": resume_id,
        "status": "applied",
    }).execute()
    return res.data[0]

async def get_applications() -> list[dict]:
    res = get_db().table("applications").select("*, resumes(name)").order("created_at", desc=True).execute()
    return res.data

async def update_application_status(app_id: str, status: str):
    get_db().table("applications").update({"status": status}).eq("id", app_id).execute()

# ── Job feed (for PWA display) ────────────────────────────────────────────────

async def save_job(job: dict):
    get_db().table("jobs").upsert({
        "job_id": job["id"],
        "company": job.get("company"),
        "role": job.get("role"),
        "location": job.get("location", ""),
        "url": job.get("url", ""),
        "source": job.get("source"),
        "ats": job.get("ats"),
        "description": job.get("description", "")[:3000],
    }, on_conflict="job_id").execute()

async def get_jobs(limit: int = 50) -> list[dict]:
    res = get_db().table("jobs").select("*").order("created_at", desc=True).limit(limit).execute()
    return res.data
