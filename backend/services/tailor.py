import logging
import anthropic
from services.config import settings

log = logging.getLogger("tailor")
client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

PROMPT = """You are an expert resume writer for tech internships.

Given a base resume and a job description, rewrite the resume tailored for that specific role.

Rules:
- NEVER invent experience, skills, or numbers
- Reorder bullets so the most relevant come first
- Mirror keywords from the JD naturally (for ATS)
- Keep it to 1 page — trim irrelevant stuff
- Adjust the summary to speak directly to this role
- Use action verbs matching the company's energy
- Output ONLY the resume text, no commentary"""

async def tailor_resume(resume_content: str, job: dict) -> str:
    jd = f"""Company: {job.get('company')}
Role: {job.get('role')}
Location: {job.get('location', '')}

{job.get('description', 'No description available')}"""

    log.info(f"Tailoring resume for {job.get('company')} — {job.get('role')}")

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"{PROMPT}\n\n---RESUME---\n{resume_content}\n\n---JOB DESCRIPTION---\n{jd}"
        }]
    )
    return msg.content[0].text
