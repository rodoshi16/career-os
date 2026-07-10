import io
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.db import (
    save_resume, get_resumes, get_resume, delete_resume,
    save_push_subscription, get_applications, update_application_status,
    log_application, get_jobs
)
from services.tailor import tailor_resume
from services.apply import apply_greenhouse, apply_lever, APPLICANT

log = logging.getLogger("routes")
router = APIRouter(prefix="/api")

# ── Jobs feed ─────────────────────────────────────────────────────────────────

@router.get("/jobs")
async def jobs():
    return await get_jobs(limit=100)

# ── Resumes ───────────────────────────────────────────────────────────────────

@router.get("/resumes")
async def list_resumes():
    return await get_resumes()

@router.post("/resumes")
async def upload_resume(file: UploadFile = File(...), name: str = "Resume"):
    content = await file.read()

    if file.filename.endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    else:
        text = content.decode("utf-8")

    if not text.strip():
        raise HTTPException(400, "Could not extract text from resume")

    resume_id = await save_resume(name, text)
    return {"id": resume_id, "name": name, "chars": len(text)}

@router.delete("/resumes/{resume_id}")
async def remove_resume(resume_id: str):
    await delete_resume(resume_id)
    return {"deleted": True}

# ── Resume tailoring ──────────────────────────────────────────────────────────

class TailorRequest(BaseModel):
    resume_id: str
    company: str
    role: str
    location: str = ""
    description: str = ""

@router.post("/tailor")
async def tailor(req: TailorRequest):
    resume = await get_resume(req.resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")
    tailored = await tailor_resume(resume["content"], req.model_dump())
    return {"tailored": tailored}

# ── One-click apply ───────────────────────────────────────────────────────────

class ApplyRequest(BaseModel):
    resume_id: str
    job_id: str        # from jobs table
    company: str
    role: str
    url: str
    source: str
    ats: str | None = None
    ats_job_id: str | None = None
    ats_slug: str | None = None

@router.post("/apply")
async def apply(req: ApplyRequest):
    resume = await get_resume(req.resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")

    result = {"success": False, "message": "Manual apply required"}

    if req.ats == "greenhouse" and req.ats_job_id and req.ats_slug:
        result = await apply_greenhouse(req.ats_job_id, req.ats_slug, resume["content"])
    elif req.ats == "lever" and req.ats_job_id and req.ats_slug:
        result = await apply_lever(req.ats_job_id, req.ats_slug, resume["content"])

    # Log it regardless of auto-apply success
    await log_application({
        "company": req.company,
        "role": req.role,
        "url": req.url,
        "source": req.source,
        "ats": req.ats,
    }, req.resume_id)

    return result

# ── Application tracker ───────────────────────────────────────────────────────

@router.get("/applications")
async def applications():
    return await get_applications()

class StatusUpdate(BaseModel):
    status: str

@router.patch("/applications/{app_id}/status")
async def update_status(app_id: str, req: StatusUpdate):
    valid = {"applied", "oa", "interview", "offer", "rejected"}
    if req.status not in valid:
        raise HTTPException(400, f"Status must be one of {valid}")
    await update_application_status(app_id, req.status)
    return {"updated": True}

# ── Web push subscription ─────────────────────────────────────────────────────

@router.post("/push/subscribe")
async def subscribe(sub: dict):
    await save_push_subscription(sub)
    return {"subscribed": True}

@router.get("/push/vapid-public-key")
async def vapid_key():
    from services.config import settings
    return {"key": settings.vapid_public_key}

# ── Applicant info (for auto-fill reference) ──────────────────────────────────

@router.get("/applicant")
async def applicant_info():
    """Returns your info so the PWA can show it / use for autofill."""
    return APPLICANT
