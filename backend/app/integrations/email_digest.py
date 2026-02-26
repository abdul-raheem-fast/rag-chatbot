"""
Email digest: send weekly summary of top questions and unanswered queries.
Uses aiosmtplib for async email sending.
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


async def send_email(to: str, subject: str, html_body: str):
    """Send an email via SMTP."""
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP not configured, skipping email")
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.email_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=True,
        )
        logger.info("Email sent", to=to, subject=subject)
    except Exception as e:
        logger.error("Failed to send email", error=str(e))


async def send_weekly_digest(
    to: str,
    total_questions: int,
    top_questions: list[str],
    unanswered: list[str],
    satisfaction_rate: float,
):
    """Send the weekly analytics digest email."""
    top_qs_html = "".join(f"<li>{q}</li>" for q in top_questions[:10])
    unanswered_html = "".join(f"<li>{q}</li>" for q in unanswered[:10])

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1a1a2e;">RAG Chatbot - Weekly Digest</h2>
        <p>Week ending {datetime.utcnow().strftime('%B %d, %Y')}</p>

        <div style="background: #f0f0f5; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <h3>Summary</h3>
            <p><strong>Total questions:</strong> {total_questions}</p>
            <p><strong>Satisfaction rate:</strong> {satisfaction_rate:.0%}</p>
        </div>

        <div style="margin: 16px 0;">
            <h3>Top Questions</h3>
            <ol>{top_qs_html or '<li>No questions this week</li>'}</ol>
        </div>

        <div style="margin: 16px 0;">
            <h3>Unanswered Questions (needs attention)</h3>
            <ol>{unanswered_html or '<li>All questions were answered!</li>'}</ol>
        </div>

        <hr style="border: none; border-top: 1px solid #ddd;">
        <p style="color: #666; font-size: 12px;">
            This is an automated digest from your RAG Chatbot.
        </p>
    </body>
    </html>
    """

    await send_email(to, f"RAG Chatbot Weekly Digest - {datetime.utcnow().strftime('%b %d')}", html)
