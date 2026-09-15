import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from typing import Optional
from app.config.settings import settings
from app.config.logging import logger

def _send_smtp_sync(to_email: str, subject: str, text_content: str, html_content: str) -> bool:
    """Synchronous RFC-compliant SMTP email delivery with SSL/STARTTLS fallback."""
    smtp_user = settings.SMTP_USER or "syntaxtrrors@gmail.com"
    smtp_pass = settings.SMTP_PASS or "szbfukaiioisvnly"
    smtp_host = settings.SMTP_HOST or "smtp.gmail.com"
    from_name = settings.SMTP_FROM_NAME or "PAIMANA Sovereign Platform"

    if not smtp_user or not smtp_pass:
        logger.warning("SMTP credentials not configured. Skipping email delivery.")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="gmail.com")

    msg.set_content(text_content)
    msg.add_alternative(html_content, subtype="html")

    # Priority 1: Direct SSL over port 465 (optimal for Gmail, avoids STARTTLS negotiation lag)
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, 465, context=ctx, timeout=12) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info(f"Email successfully delivered via SSL 465 to {to_email} with subject '{subject}'")
        return True
    except Exception as ssl_err:
        logger.warning(f"Port 465 SSL delivery failed ({ssl_err}), attempting Port 587 STARTTLS fallback...")

    # Priority 2: STARTTLS over port 587
    try:
        with smtplib.SMTP(smtp_host, 587, timeout=12) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info(f"Email successfully delivered via STARTTLS 587 to {to_email} with subject '{subject}'")
        return True
    except Exception as e:
        logger.error(f"SMTP delivery completely failed to {to_email}: {e}")
        return False

async def send_otp_email(to_email: str, code: str, purpose: str = "signup") -> bool:
    """
    Sends a 6-digit verification code to the user's official email.
    Always logs to terminal console as a fallback.
    """
    purpose_text = "verify your new PAIMANA account" if purpose == "signup" else "sign in to PAIMANA"
    print(f"\n=======================================================")
    print(f"[PAIMANA OTP] purpose={purpose} | email={to_email} | code={code}")
    print(f"=======================================================\n", flush=True)

    subject = f"Your PAIMANA verification code: {code}"
    text_content = (
        f"Your verification code is {code}. Use it to {purpose_text}. "
        f"It expires in {settings.OTP_EXPIRE_MINUTES} minutes. If you did not request this, you can ignore this email."
    )
    html_content = f"""
    <div style="font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 440px; margin: auto; padding: 28px; border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff; color: #0f172a;">
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
        <span style="font-size: 18px; font-weight: 700; letter-spacing: 0.05em; color: #1e293b;">PAIMANA</span>
        <span style="font-size: 11px; background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 999px; font-weight: 600;">OFFICIAL AUTH</span>
      </div>
      <h2 style="margin: 0 0 8px 0; color: #0f172a; font-size: 20px; font-weight: 600;">Verification Code</h2>
      <p style="color: #64748b; font-size: 14px; line-height: 1.5; margin: 0 0 20px 0;">Use this single-use 6-digit code to {purpose_text}. Valid for {settings.OTP_EXPIRE_MINUTES} minutes.</p>
      <div style="font-size: 34px; font-weight: 700; letter-spacing: 8px; text-align: center; padding: 18px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; margin: 20px 0; color: #0284c7; font-family: monospace;">
        {code}
      </div>
      <p style="color: #94a3b8; font-size: 12px; margin: 20px 0 0 0; line-height: 1.4;">
        If you did not initiate this authentication request, please inform your ministry's project administrator immediately.
      </p>
    </div>
    """
    return await asyncio.to_thread(_send_smtp_sync, to_email, subject, text_content, html_content)

async def send_account_created_email(to_email: str, full_name: str) -> bool:
    """Sends account verified confirmation email."""
    subject = "Your PAIMANA account is ready"
    text_content = f"Hi {full_name}, your PAIMANA account has been verified successfully. You can now sign in with your official credentials."
    html_content = f"""
    <div style="font-family: 'IBM Plex Sans', sans-serif; max-width: 440px; margin: auto; padding: 28px; border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff;">
      <h2 style="margin: 0 0 8px 0; color: #0f172a;">Welcome to PAIMANA</h2>
      <p style="color: #475569; font-size: 14px; line-height: 1.5;">Hi <strong>{full_name}</strong>, your account has been verified and provisioned with authorized analytical access.</p>
      <div style="margin: 20px 0; padding: 14px; background: #f0fdf4; border-left: 4px solid #22c55e; border-radius: 4px; font-size: 13px; color: #166534;">
        ✓ Identity Verified · Institutional Early-Warning Access Activated
      </div>
      <p style="color: #94a3b8; font-size: 12px;">PAIMANA National Infrastructure Decision-Support Platform</p>
    </div>
    """
    return await asyncio.to_thread(_send_smtp_sync, to_email, subject, text_content, html_content)

async def send_login_alert_email(to_email: str, time_str: str, ip_address: str = "") -> bool:
    """Sends new sign-in alert notification."""
    subject = "Security Notice: New sign-in to PAIMANA"
    text_content = f"Your PAIMANA account was signed in to at {time_str}{f' from IP {ip_address}' if ip_address else ''}."
    html_content = f"""
    <div style="font-family: 'IBM Plex Sans', sans-serif; max-width: 440px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 10px;">
      <h3 style="margin: 0 0 10px 0; color: #0f172a;">New Sign-In Detected</h3>
      <p style="color: #475569; font-size: 13.5px;">Your PAIMANA account was just accessed with valid credentials.</p>
      <table style="font-size: 13px; color: #1e293b; margin: 14px 0;">
        <tr><td style="padding: 3px 14px 3px 0; color: #64748b;">Timestamp:</td><td><strong>{time_str}</strong></td></tr>
        {f'<tr><td style="padding: 3px 14px 3px 0; color: #64748b;">Origin IP:</td><td><strong>{ip_address}</strong></td></tr>' if ip_address else ''}
      </table>
      <p style="color: #94a3b8; font-size: 11.5px;">If this was not you, please rotate your password immediately.</p>
    </div>
    """
    return await asyncio.to_thread(_send_smtp_sync, to_email, subject, text_content, html_content)
