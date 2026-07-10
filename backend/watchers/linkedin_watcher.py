import re
import logging
import hashlib
from services.config import settings
from services.db import is_seen, mark_seen, save_job
from services.notify import notify_job

log = logging.getLogger("linkedin")

class LinkedInWatcher:
    def __init__(self):
        self._api = None

    def _init(self):
        if self._api is not None:
            return
        if not settings.linkedin_email or not settings.linkedin_password:
            log.warning("LinkedIn credentials not set — skipping")
            return
        try:
            from linkedin_api import Linkedin
            self._api = Linkedin(settings.linkedin_email, settings.linkedin_password)
            log.info("LinkedIn authenticated")
        except Exception as e:
            log.error(f"LinkedIn auth failed: {e}")

    async def check(self):
        self._init()
        if not self._api:
            return

        log.info("Checking LinkedIn feed...")
        try:
            await self._check_connections()
            await self._check_company_pages()
        except Exception as e:
            log.error(f"LinkedIn check failed: {e}")

    async def _check_connections(self):
        """Check recent posts from your direct connections."""
        try:
            # Get recent posts from your network
            posts = self._api.get_feed_posts(limit=20) or []
            for post in posts:
                job = self._parse_post(post)
                if job and not await is_seen(job["id"]):
                    await mark_seen(job["id"], job)
                    await save_job(job)
                    await notify_job(job)
        except Exception as e:
            log.debug(f"Feed posts error: {e}")

    async def _check_company_pages(self):
        """Check posts from company pages you follow."""
        for company_name in settings.target_companies:
            try:
                companies = self._api.search_companies(company_name)
                if not companies:
                    continue
                company_id = companies[0].get("urn_id")
                if not company_id:
                    continue
                updates = self._api.get_company_updates(company_id, limit=5) or []
                for post in updates:
                    job = self._parse_post(post, company_name)
                    if job and not await is_seen(job["id"]):
                        await mark_seen(job["id"], job)
                        await save_job(job)
                        await notify_job(job)
            except Exception as e:
                log.debug(f"Company page {company_name}: {e}")

    def _parse_post(self, post: dict, company_override: str = None) -> dict | None:
        # Extract text
        text = ""
        for key in ["commentary", "headerText", "text"]:
            val = post.get(key, "")
            if isinstance(val, dict):
                text = val.get("text", "")
            elif isinstance(val, str):
                text = val
            if text:
                break

        if not text:
            return None

        text_lower = text.lower()

        # Must be about internships
        intern_kws = ["intern", "internship", "co-op", "applications open",
                      "now hiring", "recruiting", "we're hiring", "apply now"]
        if not any(kw in text_lower for kw in intern_kws):
            return None

        # Extract URL
        url = None
        urls = re.findall(r'https?://\S+', text)
        if urls:
            url = urls[0].rstrip(".,)")

        # Extract company
        company = company_override or "Unknown"
        if not company_override:
            author = post.get("actor", {})
            company = author.get("name", {}).get("text", "Unknown") if isinstance(author.get("name"), dict) else "Unknown"

        post_id = hashlib.md5(f"li-{text[:120]}".encode()).hexdigest()

        return {
            "id": post_id,
            "company": company,
            "role": "Internship (LinkedIn post)",
            "location": "",
            "url": url or "",
            "description": text[:1000],
            "source": "linkedin",
            "ats": None,
        }
