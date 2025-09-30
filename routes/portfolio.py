# routes/portfolio.py
import os
import json
from flask import (Blueprint, render_template, request, flash, 
                   redirect, url_for, jsonify, send_from_directory, current_app)  # ADD current_app here
from werkzeug.utils import secure_filename

from models import db, Portfolio, SiteSettings
from utils.helpers import get_current_user, allowed_file

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('auth.index'))
    return render_template('dashboard.html', user=user, portfolio=user.portfolio)

@portfolio_bp.route('/<username>')
def view_portfolio(username):
    from models import User
    user = User.query.filter_by(username=username).first_or_404()
    if not user.portfolio:
        return "This user hasn't set up their portfolio yet.", 404

    # Get site settings for copyright and footer
    site_settings = SiteSettings.query.first()
    if not site_settings:
        site_settings = SiteSettings(
            company_name='InfySkills',
            copyright_year='2025',
            copyright_text='© 2025 InfySkills. All rights reserved.',
            footer_text='Powered by InfySkills Portfolio Builder'
        )

    template_file = f"portfolio/{user.portfolio.template_id}.html"
    return render_template(template_file, p=user.portfolio, site_settings=site_settings)

@portfolio_bp.route('/preview', methods=['POST'])
def preview():
    user = get_current_user()
    if not user:
        return jsonify({
            'success': False,
            'message': 'Authentication required.'
        }), 403

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400

        template_id = data.get('template_id', 1)
        
        # Clean the data to match Portfolio columns
        valid_fields = {column.key for column in Portfolio.__table__.columns}
        cleaned_data = {k: v for k, v in data.items() if k in valid_fields}
        
        # Handle skills data
        skills = cleaned_data.get('skills')
        if skills:
            if isinstance(skills, list):
                cleaned_data['skills'] = json.dumps(skills)
            elif isinstance(skills, str):
                try:
                    parsed = json.loads(skills)
                    cleaned_data['skills'] = json.dumps(parsed) if isinstance(parsed, list) else '[]'
                except json.JSONDecodeError:
                    cleaned_data['skills'] = '[]'
        else:
            cleaned_data['skills'] = '[]'

        # Create a temporary portfolio object for preview
        preview_portfolio = Portfolio(**cleaned_data)
        
        # Convert relative URLs to absolute for preview
        if hasattr(preview_portfolio, 'profile_pic') and preview_portfolio.profile_pic:
            if preview_portfolio.profile_pic.startswith('/uploads/'):
                preview_portfolio.profile_pic = request.host_url.rstrip('/') + preview_portfolio.profile_pic
                print(f"Converted profile_pic URL: {preview_portfolio.profile_pic}")  # Debug log
            elif preview_portfolio.profile_pic.startswith('/static/'):
                preview_portfolio.profile_pic = request.host_url.rstrip('/') + preview_portfolio.profile_pic
                print(f"Converted profile_pic URL: {preview_portfolio.profile_pic}")  # Debug log
        
        if hasattr(preview_portfolio, 'resume_file') and preview_portfolio.resume_file:
            if preview_portfolio.resume_file.startswith('/uploads/'):
                preview_portfolio.resume_file = request.host_url.rstrip('/') + preview_portfolio.resume_file
                print(f"Converted resume_file URL: {preview_portfolio.resume_file}")  # Debug log
            elif preview_portfolio.resume_file.startswith('/static/'):
                preview_portfolio.resume_file = request.host_url.rstrip('/') + preview_portfolio.resume_file
                print(f"Converted resume_file URL: {preview_portfolio.resume_file}")  # Debug log
        
        template_file = f"portfolio/{template_id}.html"
        return render_template(template_file, p=preview_portfolio)

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating preview: {str(e)}'}), 400

@portfolio_bp.route('/save_portfolio', methods=['POST'])
def save_portfolio():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 403

    data = request.get_json() or {}
    portfolio = user.portfolio or Portfolio(user_id=user.id)

    for key, value in data.items():
        if hasattr(portfolio, key):
            if key == 'skills' and isinstance(value, list):
                setattr(portfolio, key, json.dumps(value))
            else:
                setattr(portfolio, key, value)

    if not user.portfolio:
        db.session.add(portfolio)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Portfolio saved successfully!'})

@portfolio_bp.route('/upload', methods=['POST'])
def upload_file():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(f"{user.id}_{file.filename}")
        upload_folder = current_app.config['UPLOAD_FOLDER']
        filepath = os.path.join(upload_folder, filename)
        os.makedirs(upload_folder, exist_ok=True)
        file.save(filepath)
        # Use the custom uploads route that matches our route definition
        url_path = f"/uploads/{filename}"
        print(f"File uploaded: {filename}, URL: {url_path}")  # Debug log
        return jsonify({'success': True, 'filepath': url_path})

    return jsonify({'success': False, 'message': 'File type not allowed'}), 400

@portfolio_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)