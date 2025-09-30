# routes/email.py
from flask import (Blueprint, render_template, request, redirect, 
                   url_for, flash, session, jsonify, current_app)
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import json
import os

from models import db, User, Portfolio
from utils.helpers import get_current_user
from utils.email_sender import send_email_verification_email, build_verification_url, send_user_credentials_email

email_bp = Blueprint('email', __name__)

# Initialize serializer within a function that has access to app context
def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

def finalize_registration_from_session():
    """Create User + Portfolio from session data after email verification"""
    reg = session.get('reg_temp')
    if not reg or not reg.get('email_verified'):
        return False

    username = reg['username']
    if User.query.filter_by(username=username).first():
        flash('Username no longer available. Please register again.', 'danger')
        session.pop('reg_temp', None)
        return False

    # Create user
    new_user = User(
        username=username,
        password_hash=reg['password_hash'],
        email=reg.get('email'),
        phone=reg.get('phone'),
        created_at=datetime.utcnow()
    )
    db.session.add(new_user)
    db.session.flush()

    # Create portfolio with college info in bio
    new_portfolio = Portfolio(user=new_user)
    college_parts = []
    if reg.get('college_name'):
        college_parts.append(f"College: {reg.get('college_name')}")
    if reg.get('college_year'):
        college_parts.append(f"Year: {reg.get('college_year')}")
    if reg.get('course_stream'):
        college_parts.append(f"Course: {reg.get('course_stream')}")
    if college_parts:
        new_portfolio.bio = " | ".join(college_parts)

    db.session.add(new_portfolio)
    db.session.commit()

    # Send user credentials via email after successful registration
    original_password = reg.get('original_password')
    if original_password:
        send_user_credentials_email(new_user.email, new_user.username, original_password)

    session.pop('reg_temp', None)
    session.pop('email_token', None)
    return True

@email_bp.route('/verify')
def verify():
    """
    Page where user can see email verification status
    """
    reg = session.get('reg_temp')
    if not reg:
        flash('No active registration flow. Please register first.', 'warning')
        return redirect(url_for('auth.register'))

    # Check expiry
    try:
        expires_at = datetime.fromisoformat(reg.get('expires_at'))
    except Exception:
        session.pop('reg_temp', None)
        flash('Registration flow invalid. Please register again.', 'danger')
        return redirect(url_for('auth.register'))

    if datetime.utcnow() > expires_at:
        session.pop('reg_temp', None)
        flash('Registration flow expired. Please register again.', 'danger')
        return redirect(url_for('auth.register'))

    email_verified = reg.get('email_verified', False)
    return render_template('verify.html', email=reg.get('email'), email_verified=email_verified)

@email_bp.route('/verify_email/<token>')
def verify_email(token):
    """
    Email verification endpoint - called when user clicks verification link
    """
    try:
        data = get_serializer().loads(token, salt='email-confirm-salt', max_age=60 * 60 * 24)  # 24 hours
    except SignatureExpired:
        flash('Verification link expired. Please register again.', 'danger')
        return redirect(url_for('auth.register'))
    except BadSignature:
        flash('Invalid verification link.', 'danger')
        return redirect(url_for('auth.register'))

    reg = session.get('reg_temp')
    if not reg:
        flash('No active registration flow. Please register first.', 'warning')
        return redirect(url_for('auth.register'))

    # Ensure token email and username match session
    if data.get('email') != reg.get('email') or data.get('username') != reg.get('username'):
        flash('Verification mismatch. Please register again.', 'danger')
        return redirect(url_for('auth.register'))

    # Set email as verified and create the account
    reg['email_verified'] = True
    session['reg_temp'] = reg

    if finalize_registration_from_session():
        flash('Your account has been created successfully! Please log in.', 'success')
        return redirect(url_for('auth.index'))
    else:
        flash('Error creating account. Please try registering again.', 'danger')
        return redirect(url_for('auth.register'))

@email_bp.route('/resend_verification', methods=['POST'])
def resend_verification():
    """
    Resend verification email if it hasn't been verified yet
    """
    reg = session.get('reg_temp')
    if not reg:
        flash('No active registration flow. Please register first.', 'warning')
        return redirect(url_for('auth.register'))

    # Check expiry
    try:
        expires_at = datetime.fromisoformat(reg.get('expires_at'))
    except Exception:
        session.pop('reg_temp', None)
        flash('Registration flow invalid. Please register again.', 'danger')
        return redirect(url_for('auth.register'))

    if datetime.utcnow() > expires_at:
        session.pop('reg_temp', None)
        flash('Registration flow expired. Please register again.', 'danger')
        return redirect(url_for('auth.register'))

    verify_type = request.form.get('type', '')

    if verify_type == 'email' and not reg.get('email_verified'):
        # Generate fresh token with consistent payload structure
        token_data = {
            'username': reg['username'],
            'email': reg['email'],
            'phone': reg.get('phone', ''),
            'college_name': reg.get('college_name', ''),
            'college_year': reg.get('college_year', ''),
            'course_stream': reg.get('course_stream', '')
        }
        
        token = get_serializer().dumps(token_data, salt='email-confirm-salt')
        
        # Update session with new token
        reg['email_token'] = token
        session['reg_temp'] = reg
        session['email_token'] = token
        session.modified = True

        email_sent = send_email_verification_email(reg['email'], token, reg['username'])
        if email_sent:
            flash('Verification email sent. Please check your inbox.', 'success')
        else:
            flash('Failed to send verification email. A fallback link was printed to logs.', 'danger')
    else:
        flash('Invalid verification type or already verified.', 'warning')

    return redirect(url_for('email.verify'))

@email_bp.route('/debug/email-config')
def debug_email_config():
    """
    Debug endpoint to check email configuration
    """
    # Only allow in development or with debug flag
    if current_app.config['ENV'] not in ['development', 'dev'] and not os.environ.get('DEBUG_ENABLED'):
        return jsonify({'error': 'Debug endpoints disabled in production'}), 403
        
    config_status = {
        'SMTP_SERVER': current_app.config.get('SMTP_SERVER'),
        'SMTP_USERNAME': current_app.config.get('SMTP_USERNAME'),
        'SMTP_PASSWORD_SET': bool(current_app.config.get('SMTP_PASSWORD')),
        'SMTP_FROM': current_app.config.get('SMTP_FROM'),
        'SMTP_PORT': current_app.config.get('SMTP_PORT'),
        'DOMAIN_URL': current_app.config.get('DOMAIN_URL'),
        'ALL_CONFIGURED': all([
            current_app.config.get('SMTP_SERVER'),
            current_app.config.get('SMTP_USERNAME'), 
            current_app.config.get('SMTP_PASSWORD')
        ])
    }
    return jsonify(config_status)

@email_bp.route('/test/email')
def test_email():
    """
    Test email sending functionality
    """
    if current_app.config['ENV'] not in ['development', 'dev'] and not os.environ.get('DEBUG_ENABLED'):
        return jsonify({'error': 'Test endpoints disabled in production'}), 403
        
    test_token = get_serializer().dumps({'test': 'data'}, salt='email-confirm-salt')
    success = send_email_verification_email(
        'test@example.com', 
        test_token, 
        'testuser'
    )
    
    return jsonify({
        'email_sent': success,
        'test_token': test_token,
        'verification_url': build_verification_url(test_token),
        'message': 'Check console for fallback link if email not sent'
    })

@email_bp.route('/api/verification-status')
def api_verification_status():
    """
    API endpoint to check verification status (for AJAX calls)
    """
    reg = session.get('reg_temp')
    if not reg:
        return jsonify({'error': 'No active registration'}), 400
        
    return jsonify({
        'email_verified': reg.get('email_verified', False),
        'email': reg.get('email'),
        'expires_at': reg.get('expires_at')
    })