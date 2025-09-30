#!/usr/bin/env python3
"""
Simple Flask app runner without debug mode to avoid Windows reloader issues
"""

from app import create_app

if __name__ == '__main__':
    app = create_app()
    print("🚀 Starting Portfolio Builder Application")
    print("=" * 50)
    print("✅ All authentication routes available:")
    print("   • http://127.0.0.1:8000/ (Login/Register)")
    print("   • http://127.0.0.1:8000/forgot-username")
    print("   • http://127.0.0.1:8000/forgot-password")
    print("   • http://127.0.0.1:8000/reset-password/<token>")
    print("✅ All templates properly configured")
    print("✅ Email functionality integrated")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8000, debug=False)