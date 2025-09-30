#!/usr/bin/env python3
"""
Site Settings Migration Script
Adds SiteSettings table for dynamic copyright and footer content
"""

from app import create_app
from extensions import db
from models import SiteSettings

def migrate_site_settings():
    """Add SiteSettings table and create default settings"""
    app = create_app()
    with app.app_context():
        try:
            # Create the SiteSettings table
            db.create_all()
            
            # Check if default settings already exist
            existing_settings = SiteSettings.query.first()
            if not existing_settings:
                # Create default site settings
                default_settings = SiteSettings(
                    company_name='InfySkills',
                    copyright_year='2025',
                    copyright_text='© 2025 InfySkills. All rights reserved.',
                    footer_text='Powered by InfySkills Portfolio Builder'
                )
                
                db.session.add(default_settings)
                db.session.commit()
                print("✅ Default site settings created successfully!")
                print(f"   Company: {default_settings.company_name}")
                print(f"   Copyright: {default_settings.copyright_text}")
            else:
                print("✅ Site settings already exist")
                print(f"   Company: {existing_settings.company_name}")
                print(f"   Copyright: {existing_settings.copyright_text}")
                
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_site_settings()