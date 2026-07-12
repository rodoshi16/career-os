from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_key: str

    # Anthropic (for resume tailoring)
    anthropic_api_key: str

    # Gmail SMTP (for email notifications)
    gmail_user: str
    gmail_app_password: str      # Gmail → Settings → 2FA → App Passwords
    notify_email: str            # where to send notifications (your email)

    # Web push (VAPID keys — generate once, see README)
    vapid_private_key: str
    vapid_public_key: str
    vapid_email: str             # mailto:you@gmail.com

    # GitHub (optional but recommended)
    github_token: Optional[str] = None

    # LinkedIn (your personal credentials)
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None

    # Your watchlist — used for LinkedIn + scraper matching
    target_companies: list[str] = [
        "Apple", "OpenAI", "Roblox", "Jane Street", "Citadel",
        "Tesla", "Snowflake", "Shopify", "SpaceX", "Stripe",
        "Notion", "Anthropic", "Coinbase", "Airbnb",
        "Microsoft", "Netflix", "Meta", "Google",
    ]

    github_repos: list[str] = [
        "SimplifyJobs/Summer2026-Internships",
        "speedyapply/2027-SWE-College-Jobs",
    ]

    # Greenhouse — these ARE the company career pages, just powered by Greenhouse
    # e.g. boards.greenhouse.io/openai = OpenAI's actual careers page
    greenhouse_companies: list[dict] = [
        {"name": "OpenAI",    "slug": "openai"},
        {"name": "Roblox",    "slug": "roblox"},
        {"name": "Figma",     "slug": "figma"},
        {"name": "Notion",    "slug": "notion"},
        {"name": "Anthropic", "slug": "anthropic"},
        {"name": "Coinbase",  "slug": "coinbase"},
        {"name": "Airbnb",    "slug": "airbnb"},
        {"name": "Snowflake", "slug": "snowflake"},
        {"name": "Shopify",   "slug": "shopify"},
        {"name": "Netflix",   "slug": "netflix"},
    ]

    # Lever — same idea, jobs.lever.co/stripe = Stripe's actual careers page
    lever_companies: list[dict] = [
        {"name": "Scale AI", "slug": "scaleai"},
        {"name": "Vercel",   "slug": "vercel"},
        {"name": "Stripe",   "slug": "stripe"},
    ]

    # Companies with custom career pages (Apple, Google, Meta etc.)
    # Scraped directly — handled by scraper_watcher.py
    scrape_targets: list[dict] = [
        {
            "name": "Apple",
            "url": "https://jobs.apple.com/en-us/search?team=internships-STDNT-INTNS",
            "selector": ".table-col-1",
        },
        {
            "name": "Google",
            "url": "https://careers.google.com/jobs/results/?employment_type=INTERN&q=software+engineer",
            "selector": ".gc-card__title",
        },
        {
            "name": "Meta",
            "url": "https://www.metacareers.com/jobs?roles[0]=intern",
            "selector": "._8sel",
        },
        {
            "name": "Microsoft",
            "url": "https://jobs.careers.microsoft.com/global/en/search?q=software+intern&l=en_us&pg=1&pgSz=20",
            "selector": ".ms-List-cell",
        },
        {
            "name": "Tesla",
            "url": "https://www.tesla.com/en_US/careers/search#/?keyword=intern&department=engineering",
            "selector": ".result-title",
        },
        {
            "name": "Jane Street",
            "url": "https://www.janestreet.com/join-jane-street/open-roles/?type=internship",
            "selector": ".open-role-title",
        },
        {
            "name": "Citadel",
            "url": "https://www.citadel.com/careers/open-opportunities/students/internships/",
            "selector": ".position-title",
        },
        {
            "name": "SpaceX",
            "url": "https://www.spacex.com/careers/jobs/?type=internship",
            "selector": ".career-title",
        },
    ]

    intern_keywords: list[str] = [
        "intern", "internship", "co-op", "coop",
        "university", "student", "2026", "2027", "summer", "winter"
    ]

    swe_keywords: list[str] = [
        "software", "engineer", "swe", "dev", "ml", "data",
        "research", "product", "infrastructure", "backend",
        "frontend", "fullstack", "platform", "systems"
    ]

    class Config:
        env_file = ".env"

settings = Settings()