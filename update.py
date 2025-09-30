# fix_all_endpoints.py
import os
import re

# Comprehensive endpoint mappings
replacements = {
    # Auth endpoints
    "url_for('index')": "url_for('auth.index')",
    "url_for('login')": "url_for('auth.login')", 
    "url_for('register')": "url_for('auth.register')",
    "url_for('logout')": "url_for('auth.logout')",
    
    # Email endpoints
    "url_for('verify')": "url_for('email.verify')",
    "url_for('resend_verification')": "url_for('email.resend_verification')",
    "url_for('verify_email')": "url_for('email.verify_email')",
    
    # Portfolio endpoints
    "url_for('dashboard')": "url_for('portfolio.dashboard')",
    "url_for('preview')": "url_for('portfolio.preview')",
    "url_for('save_portfolio')": "url_for('portfolio.save_portfolio')",
    "url_for('upload')": "url_for('portfolio.upload')",
    "url_for('view_portfolio')": "url_for('portfolio.view_portfolio')",
    
    # Admin endpoints
    "url_for('admin')": "url_for('admin.admin')",
    "url_for('admin_login')": "url_for('admin.admin_login')",
    "url_for('export_users_csv')": "url_for('admin.export_users_csv')",
    "url_for('export_portfolios_csv')": "url_for('admin.export_portfolios_csv')",
    
    # Form actions
    'action="/login"': 'action="{{ url_for(\'auth.login\') }}"',
    'action="/register"': 'action="{{ url_for(\'auth.register\') }}"',
    'action="/admin/login"': 'action="{{ url_for(\'admin.admin_login\') }}"',
    
    # Links
    'href="/"': 'href="{{ url_for(\'auth.index\') }}"',
    'href="/login"': 'href="{{ url_for(\'auth.login\') }}"',
    'href="/register"': 'href="{{ url_for(\'auth.register\') }}"',
    'href="/dashboard"': 'href="{{ url_for(\'portfolio.dashboard\') }}"',
    'href="/admin"': 'href="{{ url_for(\'admin.admin\') }}"',
    'href="/admin/login"': 'href="{{ url_for(\'admin.admin_login\') }}"',
    'href="/logout"': 'href="{{ url_for(\'auth.logout\') }}"',
}

# Update all HTML files
templates_dir = 'templates'
updated_files = []

for filename in os.listdir(templates_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(templates_dir, filename)
        print(f"Checking {filename}...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply replacements
        for old, new in replacements.items():
            if old in content:
                content = content.replace(old, new)
                print(f"  - Replaced: {old} -> {new}")
        
        # Only write if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            updated_files.append(filename)
            print(f"✓ Updated {filename}")
        else:
            print(f"✓ No changes needed for {filename}")

print(f"\nUpdated {len(updated_files)} files: {', '.join(updated_files)}")