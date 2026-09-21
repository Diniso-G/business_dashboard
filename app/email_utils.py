"""
Email digest support

Requires SMTP credentials in .env:
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=you@example.com
    SMTP_PASSWORD=your_app_password
    SMTP_FROM=you@example.com
    ENABLE_EMAIL_DIGEST=true (only starts the weekly scheduler if set)
    
Without those set, /admin/send-digests will just report which users were skipped rather than failing the whole app.
"""

import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from app.models import User, Report

def send_email(to_email: str, subject: str, body: str) -> bool:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", 587))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM", user)

    if not all([host, user, password]):
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    with smtplib.SMTP(host, port, timeout=15) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(sender, [to_email], msg.as_string())
    return True

def build_digest_test(db: Session, user: User) -> str | None:
    cutoff = datetime.utcnow() - timedelta(days=7)
    reports = (db.query(Report).filter(Report.user_id == user.id, Report.uploaded_at >= cutoff).order_by(Report.uploaded_at.desc()).all())

    if not reports:
        return None

    lines = [f"Your weekly business dashboard digest ({len(reports)} report(s) this week):", ""]
    for r in reports:
        lines.append(f"- {r.filename} (uploaded {r.uploaded_at:%Y-%m-%d}): "
                     f"total revenue ${r.total_revenue:,.2f}" if r.total_revenue is not None
                     else f"- {r.filename} (uploaded {r.uploaded_at:%Y-%m-%d})")
    return "\n".join(lines)

def send_all_digests(db: Session) -> dict:
    sent, skipped_no_data, skipped_no_smtp = [], [], []
    users = db.query(User).all()
    for user in users:
        text = build_digest_test(db, user)
        if not text:
            skipped_no_data.append(user.email)
            continue
        ok = send_email(user.email, "Your weekly dashboard digest", text)
        if ok:
            sent.append(user.email)
        else:
            skipped_no_smtp.append(user.email)
    
    return {"sent": sent, "skipped_no_activity": skipped_no_data, "skipped_smtp_not_configured": skipped_no_smtp}

