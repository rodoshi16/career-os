"""
Two notification channels:
1. Email via Gmail SMTP — reliable, always works
2. Web push — shows on iPhone lock screen via PWA
"""

import json
import logging
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pywebpush import webpush, WebPushException
from services.config import settings
from services.db import get_push_subscriptions

log = logging.getLogger("notify")

# ── Email ─────────────────────────────────────────────────────────────────────

async def send_email(subject: str, body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.gmail_user
    msg["To"] = settings.notify_email
    msg.attach(MIMEText(body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=465,
            username=settings.gmail_user,
            password=settings.gmail_app_password,
            use_tls=True,
        )
        log.info(f"📧 Email sent: {subject}")
    except Exception as e:
        log.error(f"Email failed: {e}")


# ── Web push ──────────────────────────────────────────────────────────────────

async def send_web_push(title: str, body: str, url: str = "/"):
    subs = await get_push_subscriptions()
    if not subs:
        log.warning("No push subscriptions registered yet")
        return

    payload = json.dumps({"title": title, "body": body, "url": url})

    for sub in subs:
        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": f"mailto:{settings.vapid_email}"},
            )
        except WebPushException as e:
            log.error(f"Web push failed: {e}")


# ── Combined job notification ─────────────────────────────────────────────────

async def notify_job(job: dict):
    source_label = {
        "github": "📋 GitHub",
        "greenhouse": "🏢 Career Page",
        "lever": "🏢 Career Page",
        "linkedin": "💼 LinkedIn",
    }.get(job.get("source", ""), "🚨 New")

    title = f"{job['company']} — {job['role']}"
    push_body = f"{source_label} • {job.get('location', '')} • Tap to apply"

    email_body = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
        <h2 style="color:#16a34a">🎯 {job['company']}</h2>
        <h3 style="margin:0">{job['role']}</h3>
        <p style="color:#666">{source_label} • {job.get('location', 'Location TBD')}</p>
        <a href="{job.get('url', '#')}" 
           style="display:inline-block;background:#16a34a;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;margin-top:8px">
            Apply Now →
        </a>
        <p style="color:#999;font-size:12px;margin-top:20px">
            InternshipRadar • <a href="{job.get('url', '')}">Direct link</a>
        </p>
    </div>
    """

    # Fire both simultaneously
    import asyncio
    await asyncio.gather(
        send_email(f"🎯 {title}", email_body),
        send_web_push(title, push_body, job.get("url", "/")),
        return_exceptions=True
    )
