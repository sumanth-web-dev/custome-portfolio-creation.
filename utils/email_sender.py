# utils/email_sender.py
import smtplib
import os
from email.message import EmailMessage
from itsdangerous import URLSafeTimedSerializer
from flask import url_for, current_app

def build_verification_url(token):
    """Build an absolute verification URL"""
    try:
        # FIX: Changed from 'auth.verify_email' to 'email.verify_email'
        link = url_for('email.verify_email', token=token, _external=True)
        if link:
            return link
    except RuntimeError:
        pass
    # Fallback
    return f"{current_app.config['DOMAIN_URL'].rstrip('/')}{url_for('email.verify_email', token=token)}"

def send_email_verification_email(recipient_email, token, username):
    """Send verification email with fallback to console logging"""
    verify_url = build_verification_url(token)
    subject = "Verify your email address"
    body = f"Hi {username},\n\nPlease verify your email by clicking the link below:\n\n{verify_url}\n\nIf you did not request this, ignore.\n\nThanks."

    # Check SMTP configuration
    smtp_config = [
        current_app.config['SMTP_SERVER'],
        current_app.config['SMTP_USERNAME'],
        current_app.config['SMTP_PASSWORD']
    ]
    
    # Fallback to console if SMTP not configured
    if not all(smtp_config):
        current_app.logger.info(f"[DEV] SMTP not configured; printing verification link:")
        current_app.logger.info(f"[DEV] Email verification link for {recipient_email}: {verify_url}")
        print(f"VERIFICATION LINK: {verify_url}")
        return True

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = current_app.config['SMTP_FROM']
        msg['To'] = recipient_email
        msg.set_content(body)

        smtp_server = current_app.config['SMTP_SERVER']
        smtp_port = current_app.config['SMTP_PORT']

        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.ehlo()
            if smtp_port == 587:
                server.starttls()
                server.ehlo()

        server.login(current_app.config['SMTP_USERNAME'], current_app.config['SMTP_PASSWORD'])
        server.send_message(msg)
        server.quit()

        current_app.logger.info(f"Verification email sent to {recipient_email}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email: {e}", exc_info=True)
        current_app.logger.info(f"[FALLBACK] Verification link for {recipient_email}: {verify_url}")
        print(f"EMAIL SEND FAILED - FALLBACK LINK: {verify_url}")
        return False

def send_forgot_username_email(recipient_email, username):
    """Send forgot username email"""
    subject = "Your Portfolio Builder Username"
    body = f"""Hi there,

You requested your username for Portfolio Builder.

Your username is: {username}

You can log in at: {current_app.config.get('DOMAIN_URL', 'http://localhost:8000')}

If you did not request this, please ignore this email.

Best regards,
Portfolio Builder Team"""

    return send_email(recipient_email, subject, body)

def send_forgot_password_email(recipient_email, token, username):
    """Send forgot password reset email"""
    try:
        reset_url = url_for('auth.reset_password', token=token, _external=True)
    except RuntimeError:
        reset_url = f"{current_app.config.get('DOMAIN_URL', 'http://localhost:8000')}/reset-password/{token}"
    
    subject = "Reset Your Password - Portfolio Builder"
    body = f"""Hi {username},

You requested a password reset for your Portfolio Builder account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request this, please ignore this email.

Best regards,
Portfolio Builder Team"""

    return send_email(recipient_email, subject, body)

def send_user_credentials_email(recipient_email, username, password):
    """Send user credentials after successful registration"""
    subject = "Welcome to Portfolio Builder - Your Account Details"
    body = f"""Welcome to Portfolio Builder!

Your account has been successfully created. Here are your login credentials:

Username: {username}
Password: {password}
Login URL: {current_app.config.get('DOMAIN_URL', 'http://localhost:8000')}

Please keep this information secure and consider changing your password after your first login.

You can now create your professional portfolio by logging in to the dashboard.

Best regards,
Portfolio Builder Team"""

    return send_email(recipient_email, subject, body)

def send_email(recipient_email, subject, body):
    """Generic email sending function with fallback to console"""
    # Check SMTP configuration
    smtp_config = [
        current_app.config.get('SMTP_SERVER'),
        current_app.config.get('SMTP_USERNAME'),
        current_app.config.get('SMTP_PASSWORD')
    ]
    
    # Fallback to console if SMTP not configured
    if not all(smtp_config):
        current_app.logger.info(f"[DEV] SMTP not configured; printing email:")
        current_app.logger.info(f"[DEV] To: {recipient_email}")
        current_app.logger.info(f"[DEV] Subject: {subject}")
        current_app.logger.info(f"[DEV] Body: {body}")
        print(f"EMAIL TO {recipient_email}:")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print("-" * 50)
        return True

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = current_app.config.get('SMTP_FROM', 'noreply@portfoliobuilder.com')
        msg['To'] = recipient_email
        msg.set_content(body)

        smtp_server = current_app.config.get('SMTP_SERVER')
        smtp_port = current_app.config.get('SMTP_PORT', 587)

        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.ehlo()
            if smtp_port == 587:
                server.starttls()
                server.ehlo()

        server.login(current_app.config['SMTP_USERNAME'], current_app.config['SMTP_PASSWORD'])
        server.send_message(msg)
        server.quit()

        current_app.logger.info(f"Email sent to {recipient_email}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}", exc_info=True)
        print(f"EMAIL SEND FAILED TO {recipient_email}")
        return False