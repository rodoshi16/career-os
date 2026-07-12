"""
Scrapes career pages for companies that don't use Greenhouse or Lever.
Apple, Google, Meta, Microsoft, Tesla, Jane Street, Citadel, SpaceX.
Checks every 15 min — detects new job titles appearing on the page.
"""

import hashlib
import logging
import httpx
from bs4 import BeautifulSoup
from services.config import settings
from services.db import is_seen, mark_seen, save_job
from services.notify import notify_job

log = logging.getLogger("scraper")

class ScraperWatcher:
    def __init__(self):
        # Store last seen job titles per company for diffing
        self._last_titles: dict[str, set] = {}

    async def check(self):
        log.info("Checking custom career pages...")
        async with httpx.AsyncClient(
            timeout=20,
            headers={
                # Pretend to be a real browser so we don't get blocked
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
            follow_redirects=True,
        ) as client:
            for target in settings.scrape_targets:
                try:
                    await self._check_target(client, target)
                except Exception as e:
                    log.error(f"  {target['name']}: {e}")

    async def _check_target(self, client: httpx.AsyncClient, target: dict):
        resp = await client.get(target["url"])
        if resp.status_code != 200:
            log.warning(f"  {target['name']}: HTTP {resp.status_code}")
            return

        soup = BeautifulSoup(resp.text, "html.parser")
        elements = soup.select(target["selector"])
        titles = {el.get_text(strip=True) for el in elements if el.get_text(strip=True)}

        # Filter for intern/SWE roles
        filtered = {
            t for t in titles
            if any(k in t.lower() for k in settings.intern_keywords)
            and any(k in t.lower() for k in settings.swe_keywords)
        }

        company = target["name"]

        # First run — initialize, don't notify
        if company not in self._last_titles:
            self._last_titles[company] = filtered
            log.info(f"  {company}: initialized with {len(filtered)} intern roles")
            return

        # Find newly appeared titles
        new_titles = filtered - self._last_titles[company]
        self._last_titles[company] = filtered

        if not new_titles:
            return

        log.info(f"  {company}: {len(new_titles)} new roles!")

        for title in new_titles:
            job_id = hashlib.md5(f"scrape-{company}-{title}".encode()).hexdigest()
            job = {
                "id": job_id,
                "company": company,
                "role": title,
                "location": "",
                "url": target["url"],  # Links to the careers page
                "description": f"New posting detected on {company} careers page.",
                "source": "scraper",
                "ats": None,
            }
            if not await is_seen(job_id):
                await mark_seen(job_id, job)
                await save_job(job)
                await notify_job(job)
                log.info(f"  🔔 {company}: {title}")