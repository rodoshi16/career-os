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

    # Your watchlist — edit freely
    target_companies: list[str] = [
        "Apple", "OpenAI", "Roblox", "Stripe", "Figma",
        "Notion", "Anthropic", "Coinbase", "Airbnb", "Scale AI"
    ]

    github_repos: list[str] = [
        "SimplifyJobs/Summer2025-Internships",
        "SimplifyJobs/New-Grad-Positions",
    ]

    # Greenhouse slugs for your target companies
    # Find at: boards.greenhouse.io/{slug}
    greenhouse_companies: list[dict] = [
        {"name": "OpenAI",    "slug": "openai"},
        {"name": "Roblox",    "slug": "roblox"},
        {"name": "Figma",     "slug": "figma"},
        {"name": "Notion",    "slug": "notion"},
        {"name": "Anthropic", "slug": "anthropic"},
        {"name": "Coinbase",  "slug": "coinbase"},
        {"name": "Airbnb",    "slug": "airbnb"},
    ]

    # Lever slugs for your target companies
    # Find at: jobs.lever.co/{slug}
    lever_companies: list[dict] = [
        {"name": "Scale AI", "slug": "scaleai"},
        {"name": "Vercel",   "slug": "vercel"},
        {"name": "Stripe",   "slug": "stripe"},
    ]

    intern_keywords: list[str] = [
        "intern", "internship", "co-op", "coop",
        "new grad", "university", "student", "2026", "2027"
    ]

    swe_keywords: list[str] = [
        "software", "engineer", "swe", "dev", "ml", "data",
        "research", "product", "infrastructure", "backend",
        "frontend", "fullstack", "platform", "systems"
    ]

    class Config:
        env_file = ".env"

settings = Settings()
