import logging
import hashlib
import httpx
from services.config import settings
from services.db import is_seen, mark_seen, save_job
from services.notify import notify_job

log = logging.getLogger("careers")

class CareersWatcher:
    async def check(self):
        log.info("Checking career pages...")
        async with httpx.AsyncClient(timeout=15) as client:
            for company in settings.greenhouse_companies:
                try:
                    await self._check_greenhouse(client, company)
                except Exception as e:
                    log.error(f"  Greenhouse {company['name']}: {e}")

            for company in settings.lever_companies:
                try:
                    await self._check_lever(client, company)
                except Exception as e:
                    log.error(f"  Lever {company['name']}: {e}")

    async def _check_greenhouse(self, client: httpx.AsyncClient, company: dict):
        url = f"https://boards-api.greenhouse.io/v1/boards/{company['slug']}/jobs"
        resp = await client.get(url, params={"content": "true"})
        resp.raise_for_status()
        jobs = resp.json().get("jobs", [])

        intern_jobs = [j for j in jobs if self._is_intern_swe(j["title"])]
        log.info(f"  {company['name']} (Greenhouse): {len(intern_jobs)} intern roles")

        for j in intern_jobs:
            location = j.get("offices", [{}])[0].get("name", "") if j.get("offices") else ""
            job = {
                "id": hashlib.md5(f"gh-{j['id']}".encode()).hexdigest(),
                "company": company["name"],
                "role": j["title"],
                "location": location,
                "url": j.get("absolute_url", ""),
                "description": j.get("content", "")[:3000],
                "source": "greenhouse",
                "ats": "greenhouse",
                "ats_job_id": str(j["id"]),
                "ats_slug": company["slug"],
            }
            if not await is_seen(job["id"]):
                await mark_seen(job["id"], job)
                await save_job(job)
                await notify_job(job)

    async def _check_lever(self, client: httpx.AsyncClient, company: dict):
        url = f"https://api.lever.co/v0/postings/{company['slug']}"
        resp = await client.get(url, params={"mode": "json"})
        resp.raise_for_status()
        postings = resp.json()

        intern_postings = [p for p in postings if self._is_intern_swe(p["text"])]
        log.info(f"  {company['name']} (Lever): {len(intern_postings)} intern roles")

        for p in intern_postings:
            location = p.get("categories", {}).get("location", "")
            desc = ""
            for section in p.get("descriptionBody", {}).get("descriptionBodyFields", []):
                desc += section.get("text", "") + "\n"

            job = {
                "id": hashlib.md5(f"lv-{p['id']}".encode()).hexdigest(),
                "company": company["name"],
                "role": p["text"],
                "location": location,
                "url": p.get("hostedUrl", ""),
                "description": desc[:3000],
                "source": "lever",
                "ats": "lever",
                "ats_job_id": p["id"],
                "ats_slug": company["slug"],
            }
            if not await is_seen(job["id"]):
                await mark_seen(job["id"], job)
                await save_job(job)
                await notify_job(job)

    def _is_intern_swe(self, title: str) -> bool:
        t = title.lower()
        is_intern = any(k in t for k in settings.intern_keywords)
        is_swe = any(k in t for k in settings.swe_keywords)
        return is_intern and is_swe
