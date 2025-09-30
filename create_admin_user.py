#!/usr/bin/env python3
"""
Quick script to create an admin user
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

def create_admin_user():
    app = create_app()
    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        
        if admin_user:
            print("Admin user already exists!")
            print(f"Username: admin")
            print(f"Password: admin123")
            print(f"User ID: {admin_user.id}")
            return
        
        # Create admin user
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            email='admin@example.com',
            is_admin=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("Admin user created successfully!")
        print(f"Username: admin")
        print(f"Password: admin123")
        print(f"User ID: {admin_user.id}")

if __name__ == '__main__':
    create_admin_user()