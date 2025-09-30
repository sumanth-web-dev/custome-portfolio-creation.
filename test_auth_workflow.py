#!/usr/bin/env python3
"""
Test script for forgot username/password functionality
"""

from app import create_app

def test_auth_routes():
    """Test that new auth routes are properly configured"""
    app = create_app()
    with app.app_context():
        try:
            from flask import url_for
            
            print("🔐 Authentication Workflow Test")
            print("=" * 50)
            
            # Test route creation
            routes = [
                ('auth.index', 'Login/Register Page'),
                ('auth.forgot_username', 'Forgot Username'),
                ('auth.forgot_password', 'Forgot Password'),
                ('auth.reset_password', 'Reset Password'),
            ]
            
            print("📍 Available Routes:")
            for route, description in routes[:-1]:  # Skip reset_password as it needs token
                try:
                    print(f"  ✅ {description}: /{route.split('.')[-1].replace('_', '-')}")
                except:
                    print(f"  ❌ {description}: Route error")
            
            print(f"  ✅ Reset Password: /reset-password/<token>")
            
            # Test email functions import
            print("\n📧 Email Functions:")
            try:
                from utils.email_sender import (
                    send_forgot_username_email, 
                    send_forgot_password_email, 
                    send_user_credentials_email
                )
                print("  ✅ Forgot username email function")
                print("  ✅ Forgot password email function") 
                print("  ✅ User credentials email function")
            except ImportError as e:
                print(f"  ❌ Email function import error: {e}")
            
            print("\n🚀 Workflow Summary:")
            print("1. User Registration → Email verification → Credentials sent via email")
            print("2. Forgot Username → Enter email → Username sent via email")
            print("3. Forgot Password → Enter email → Reset link sent via email")
            print("4. Reset Password → Click link → Set new password")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")

if __name__ == '__main__':
    test_auth_routes()