#!/usr/bin/env python3
"""
Script to update the database schema to match the new Portfolio model
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Portfolio
import json

def migrate_database():
    app = create_app()
    with app.app_context():
        # Drop and recreate all tables to match new schema
        print("Updating database schema...")
        db.drop_all()
        db.create_all()
        
        # Create default admin user
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', email='admin@example.com', is_admin=True)
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            print("Created admin user: admin/admin123")
        
        # Create test user
        if not User.query.filter_by(username='testuser').first():
            test_user = User(username='testuser', email='test@example.com', phone='1234567890')
            test_user.set_password('testpass')
            db.session.add(test_user)
            
            # Create default portfolio for test user
            test_portfolio = Portfolio(
                user=test_user,
                template_id=1,
                full_name='Test User',
                company_name='Test Company',
                job_title='Developer',
                bio='This is a test portfolio',
                email='test@example.com',
                phone='1234567890',
                skills='["HTML", "CSS", "JavaScript", "Python"]',
                project1_title='Sample Project 1',
                project1_desc='Description of sample project 1',
                project1_link='#',
                project2_title='Sample Project 2',
                project2_desc='Description of sample project 2',
                project2_link='#',
                project3_title='Sample Project 3',
                project3_desc='Description of sample project 3',
                project3_link='#'
            )
            db.session.add(test_portfolio)
            print("Created test user: testuser/testpass with sample portfolio")
        
        db.session.commit()
        print("Database migration completed successfully!")

if __name__ == '__main__':
    migrate_database()