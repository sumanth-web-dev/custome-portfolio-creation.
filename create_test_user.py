#!/usr/bin/env python3
"""
Quick script to create a test user for testing template switching
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

def create_test_user():
    app = create_app()
    with app.app_context():
        # Check if test user already exists
        test_user = User.query.filter_by(username='testuser').first()
        
        if test_user:
            print("Test user already exists!")
            print(f"Username: testuser")
            print(f"Password: testpass")
            print(f"User ID: {test_user.id}")
            return
        
        # Create test user
        test_user = User(
            username='testuser',
            password_hash=generate_password_hash('testpass'),
            email='test@example.com',
            phone='1234567890',
            is_admin=False
        )
        
        db.session.add(test_user)
        db.session.commit()
        
        print("Test user created successfully!")
        print(f"Username: testuser")
        print(f"Password: testpass")
        print(f"User ID: {test_user.id}")

if __name__ == '__main__':
    create_test_user()