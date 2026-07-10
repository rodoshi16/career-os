"""
One-click apply for Greenhouse and Lever ATS.
These have public APIs that accept applications programmatically.
"""

import logging
import httpx
from services.db import get_resume

log = logging.getLogger("apply")

# Your personal info — fill these in
APPLICANT = {
    "first_name": "Your",
    "last_name": "Name",
    "email": "you@email.com",
    "phone": "+1234567890",
    "linkedin": "https://linkedin.com/in/yourprofile",
    "github": "https://github.com/yourusername",
    "website": "",
    "grad_year": "2026",
    "school": "Your University",
    "degree": "Bachelor of Science",
    "major": "Computer Science",
}

async def apply_greenhouse(job_id: str, slug: str, resume_content: str) -> dict:
    """
    Submit application to Greenhouse via their API.
    Returns {"success": True/False, "message": "..."}
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}"

    # Build multipart form data
    import io
    resume_bytes = resume_content.encode("utf-8")

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}/applications",
                data={
                    "first_name": APPLICANT["first_name"],
                    "last_name": APPLICANT["last_name"],
                    "email": APPLICANT["email"],
                    "phone": APPLICANT["phone"],
                    "resume_text": resume_content,
                    "cover_letter_text": "",
                    "question_12345": APPLICANT["linkedin"],  # LinkedIn URL field (varies by company)
                },
                files={
                    "resume": ("resume.pdf", resume_bytes, "application/pdf"),
                }
            )

            if resp.status_code in (200, 201):
                log.info(f"✅ Greenhouse apply success: {slug}/{job_id}")
                return {"success": True, "message": "Applied successfully via Greenhouse"}
            else:
                log.error(f"Greenhouse apply failed {resp.status_code}: {resp.text[:200]}")
                return {"success": False, "message": f"Greenhouse returned {resp.status_code}"}

        except Exception as e:
            log.error(f"Greenhouse apply error: {e}")
            return {"success": False, "message": str(e)}


async def apply_lever(posting_id: str, slug: str, resume_content: str) -> dict:
    """
    Submit application to Lever via their apply API.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"https://api.lever.co/v0/postings/{slug}/{posting_id}/apply",
                data={
                    "name": f"{APPLICANT['first_name']} {APPLICANT['last_name']}",
                    "email": APPLICANT["email"],
                    "phone": APPLICANT["phone"],
                    "org": APPLICANT["school"],
                    "urls[LinkedIn]": APPLICANT["linkedin"],
                    "urls[GitHub]": APPLICANT["github"],
                    "resume": resume_content,
                },
            )

            if resp.status_code in (200, 201):
                log.info(f"✅ Lever apply success: {slug}/{posting_id}")
                return {"success": True, "message": "Applied successfully via Lever"}
            else:
                log.error(f"Lever apply failed {resp.status_code}: {resp.text[:200]}")
                return {"success": False, "message": f"Lever returned {resp.status_code}"}

        except Exception as e:
            log.error(f"Lever apply error: {e}")
            return {"success": False, "message": str(e)}
