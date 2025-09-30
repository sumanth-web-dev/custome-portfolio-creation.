# routes/auth.py
from flask import (Blueprint, render_template, request, redirect, 
                   url_for, flash, session, current_app)  # Make sure current_app is imported
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from itsdangerous import URLSafeTimedSerializer
import secrets
import string

from models import db, User
from utils.helpers import get_current_user
from utils.email_sender import send_email_verification_email, send_forgot_username_email, send_forgot_password_email, send_user_credentials_email
from flask_login import login_user,login_required,logout_user, current_user

auth_bp = Blueprint('auth', __name__)

def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

@auth_bp.route('/')
def index():
    return render_template('index.html')

@auth_bp.route('/test-template-switching')
def test_template_switching():
    with open('test_template_switching.html', 'r') as f:
        return f.read()

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        college_name = request.form.get('college_name', '').strip()
        college_year = request.form.get('college_year', '').strip()
        course_stream = request.form.get('course_stream', '').strip()

        # Validation
        if not username or not password or not email:
            flash('Username, password, and email are required.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('auth.register'))

        # Prepare temporary registration
        temp = {
            'username': username,
            'password_hash': generate_password_hash(password),
            'original_password': password,  # Store original password for email
            'is_admin': False,
            'phone': phone,
            'email': email,
            'college_name': college_name,
            'college_year': college_year,
            'course_stream': course_stream,
            'email_verified': False,
            'created_at': datetime.utcnow().isoformat()
        }

        # Generate email token
        token_data = {
            'username': username,
            'email': email,
            'phone': phone,
            'college_name': college_name,
            'college_year': college_year,
            'course_stream': course_stream
        }
        
        from itsdangerous import URLSafeTimedSerializer
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = serializer.dumps(token_data, salt='email-confirm-salt')

        email_sent = send_email_verification_email(email, token, username)

        # Save to session
        temp['email_token'] = token
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        temp['expires_at'] = expires_at.isoformat()
        session['reg_temp'] = temp
        session['email_token'] = token

        if not email_sent:
            flash('Verification email sending failed. Check logs for fallback link.', 'warning')
        else:
            flash('Verification email sent. Please check your inbox.', 'info')

        # Redirect to email verification page
        return redirect(url_for('email.verify'))

    return render_template('index.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        login_user(user)
        session.permanent = True
        session['user_id'] = user.id
        session['logged_in_time'] = datetime.utcnow().isoformat()

        user.last_login = datetime.utcnow()
        db.session.commit()

        if user.is_admin:
            return redirect(url_for('admin.admin'))
        return redirect(url_for('portfolio.dashboard'))
    else:
        flash('Invalid username or password.', 'danger')
        return redirect(url_for('auth.index'))

@auth_bp.route('/forgot-username', methods=['GET', 'POST'])
def forgot_username():
    """Handle forgot username requests"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Email address is required.', 'danger')
            return render_template('forgot_username.html')
        
        user = User.query.filter_by(email=email).first()
        if user:
            # Send username to email
            email_sent = send_forgot_username_email(user.email, user.username)
            if email_sent:
                flash('Your username has been sent to your email address.', 'success')
            else:
                flash('Failed to send email. Please try again later.', 'danger')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, the username has been sent.', 'info')
        
        return redirect(url_for('auth.index'))
    
    return render_template('forgot_username.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Email address is required.', 'danger')
            return render_template('forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate password reset token
            serializer = get_serializer()
            token = serializer.dumps(user.email, salt='password-reset-salt')
            
            # Send reset link to email
            email_sent = send_forgot_password_email(user.email, token, user.username)
            if email_sent:
                flash('Password reset link has been sent to your email address.', 'success')
            else:
                flash('Failed to send email. Please try again later.', 'danger')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, a reset link has been sent.', 'info')
        
        return redirect(url_for('auth.index'))
    
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    try:
        serializer = get_serializer()
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)  # 1 hour expiry
    except:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.index'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid reset link.', 'danger')
        return redirect(url_for('auth.index'))
    
    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not new_password or len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('auth.index'))
    
    return render_template('reset_password.html', token=token, user=user)


@auth_bp.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.index'))