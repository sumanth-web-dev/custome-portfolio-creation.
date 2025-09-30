# utils/helpers.py
import os
import json
from flask import session, current_app
from datetime import datetime
from models import User

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def get_current_user():
    if 'user_id' in session:
        try:
            return User.query.get(int(session['user_id']))
        except Exception:
            return None
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_session():
    """Validate user session on each request"""
    if 'user_id' in session:
        try:
            user = User.query.get(int(session['user_id']))
            if not user:
                session.clear()
            else:
                session['last_active'] = datetime.utcnow().isoformat()
        except Exception:
            session.clear()