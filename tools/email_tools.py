"""
tools/email_tools.py — NayePankh AI Workforce
===============================================
Email sending via SMTP. In development mode, emails are
logged to SQLite instead of actually sent.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM, APP_ENV
from memory.db import execute_query

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body_html: str, body_text: str = None) -> dict:
    """
    Send an email. In development, logs instead of sending.

    Args:
        to:        Recipient email address
        subject:   Email subject
        body_html: HTML body content
        body_text: Plain text fallback (optional)

    Returns:
        {"success": bool, "message": str}
    """
    if APP_ENV == "development" or not SMTP_USER:
        return log_email_event(to, subject, body_html, status="simulated")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_FROM
        msg["To"]      = to

        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to, msg.as_string())

        log_email_event(to, subject, body_html, status="sent")
        return {"success": True, "message": f"Email sent to {to}"}
    except Exception as e:
        log_email_event(to, subject, body_html, status="failed", error=str(e))
        logger.error(f"[Email] Failed to send to {to}: {e}")
        return {"success": False, "message": str(e)}


def log_email_event(to: str, subject: str, body: str,
                    status: str = "sent", error: str = None) -> dict:
    """
    Log an email event to the tasks table for audit trail.
    """
    try:
        import json
        execute_query(
            "INSERT INTO tasks (agent, task_type, status, payload, result) "
            "VALUES ('email_tool', 'send_email', ?, ?, ?)",
            (
                "done" if status in ("sent", "simulated") else "failed",
                json.dumps({"to": to, "subject": subject}),
                json.dumps({"status": status, "error": error}),
            ),
            fetch="none",
        )
        return {"success": True, "message": f"Email {status} to {to}"}
    except Exception as e:
        logger.error(f"[Email] Log failed: {e}")
        return {"success": False, "message": str(e)}


# ── Pre-built email templates ────────────────────────────────

def send_volunteer_welcome(name: str, email: str) -> dict:
    """Send welcome email to newly registered volunteer."""
    subject = f"Welcome to NayePankh, {name}! 🕊️"
    body_html = f"""
    <h2>Welcome aboard, {name}!</h2>
    <p>We're thrilled to have you join the NayePankh volunteer family.</p>
    <p><strong>Next Steps:</strong></p>
    <ul>
        <li>Attend the next orientation (every 1st Saturday, 11 AM IST)</li>
        <li>Sign the Volunteer Code of Conduct</li>
        <li>Connect with your team coordinator</li>
    </ul>
    <p>Together, we spread wings and change lives! 💛</p>
    <p>— The NayePankh Team</p>
    """
    return send_email(email, subject, body_html)


def send_intern_offer_letter(name: str, email: str, program: str,
                             start_date: str, mentor_name: str) -> dict:
    """Send offer letter to an accepted intern."""
    subject = f"🎉 Internship Offer — NayePankh Foundation | {program}"
    body_html = f"""
    <h2>Dear {name},</h2>
    <p>Congratulations! We are pleased to offer you an internship position at <strong>NayePankh Foundation</strong>.</p>
    <p><strong>Program:</strong> {program}<br>
    <strong>Start Date:</strong> {start_date}<br>
    <strong>Your Mentor:</strong> {mentor_name}</p>
    <p>Please confirm your acceptance by replying to this email within 48 hours.</p>
    <p>Looking forward to working with you! 🚀</p>
    <p>— NayePankh Internship Team</p>
    """
    return send_email(email, subject, body_html)


def send_certificate_notification(name: str, email: str, certificate_url: str) -> dict:
    """Notify intern that their certificate is ready."""
    subject = "🏆 Your NayePankh Internship Certificate is Ready!"
    body_html = f"""
    <h2>Congratulations, {name}!</h2>
    <p>You have successfully completed your internship at <strong>NayePankh Foundation</strong>.</p>
    <p>Your certificate is ready: <a href="{certificate_url}">Download Certificate</a></p>
    <p>We are proud of everything you've accomplished. Wishing you great success ahead! 🌟</p>
    <p>— NayePankh Team</p>
    """
    return send_email(email, subject, body_html)
