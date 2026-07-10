import re
import logging
import hashlib
import httpx
from services.config import settings
from services.db import is_seen, mark_seen, save_job
from services.notify import notify_job

log = logging.getLogger("github")
GITHUB_API = "https://api.github.com"

class GitHubWatcher:
    def __init__(self):
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if settings.github_token:
            self.headers["Authorization"] = f"token {settings.github_token}"
        self._last_sha: dict[str, str] = {}

    async def check(self):
        log.info("Checking GitHub repos...")
        for repo in settings.github_repos:
            try:
                await self._check_repo(repo)
            except Exception as e:
                log.error(f"GitHub {repo}: {e}")

    async def _check_repo(self, repo: str):
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{GITHUB_API}/repos/{repo}/commits",
                headers=self.headers,
                params={"per_page": 1}
            )
            resp.raise_for_status()
            commits = resp.json()
            if not commits:
                return

            latest_sha = commits[0]["sha"]

            if repo not in self._last_sha:
                self._last_sha[repo] = latest_sha
                log.info(f"  {repo}: initialized at {latest_sha[:7]}")
                return

            if latest_sha == self._last_sha[repo]:
                return

            log.info(f"  {repo}: new commit {latest_sha[:7]}")
            self._last_sha[repo] = latest_sha

            diff_resp = await client.get(
                f"{GITHUB_API}/repos/{repo}/commits/{latest_sha}",
                headers=self.headers,
            )
            diff_resp.raise_for_status()
            commit_data = diff_resp.json()

            new_jobs = []
            for file in commit_data.get("files", []):
                if file.get("filename", "").endswith(".md"):
                    new_jobs.extend(self._parse_patch(file.get("patch", ""), repo))

            log.info(f"  {repo}: {len(new_jobs)} new jobs")
            for job in new_jobs:
                if not await is_seen(job["id"]):
                    await mark_seen(job["id"], job)
                    await save_job(job)
                    await notify_job(job)

    def _parse_patch(self, patch: str, repo: str) -> list[dict]:
        jobs = []
        for line in patch.split("\n"):
            if not line.startswith("+"):
                continue
            line = line[1:].strip()
            if not (line.startswith("|") and "http" in line):
                continue
            if "---" in line or "Company" in line:
                continue

            job = self._parse_row(line, repo)
            if job:
                title_lower = f"{job['company']} {job['role']}".lower()
                is_intern = any(k in title_lower for k in settings.intern_keywords)
                is_swe = any(k in title_lower for k in settings.swe_keywords)
                is_target = any(c.lower() in title_lower for c in settings.target_companies)
                if (is_intern and is_swe) or is_target:
                    jobs.append(job)
        return jobs

    def _parse_row(self, row: str, repo: str) -> dict | None:
        cols = [c.strip() for c in row.split("|") if c.strip()]
        if len(cols) < 3:
            return None

        company = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cols[0]).strip()
        role = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cols[1]).strip()
        location = cols[2] if len(cols) > 2 else ""

        links = re.findall(r'\(([^)]+)\)', row)
        url = next((l for l in links if l.startswith("http")), None)

        if not company or not role:
            return None

        return {
            "id": hashlib.md5(f"gh-{company}-{role}".encode()).hexdigest(),
            "company": company,
            "role": role,
            "location": location,
            "url": url,
            "source": "github",
            "ats": None,
        }
