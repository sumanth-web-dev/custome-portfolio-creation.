# routes/admin.py
import csv
import json
from io import StringIO
from flask import (Blueprint, render_template, request, redirect, 
                   url_for, flash, make_response, session, jsonify)
from datetime import datetime, timedelta


from models import db, User, Portfolio, SiteSettings
from utils.helpers import get_current_user


from flask_login import login_user,login_required, logout_user, current_user



admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.is_admin and user.check_password(password):
            session['user_id'] = user.id
            flash('Admin login successful.', 'success')
            return redirect(url_for('admin.admin'))
        else:
            flash('Invalid admin credentials.', 'danger')
            return redirect(url_for('admin.admin_login'))
    return render_template('admin_login.html')

@admin_bp.route('/admin')
@login_required
def admin():
    user = get_current_user()
    if not user or not user.is_admin:
        return redirect(url_for('admin.admin_login'))

    all_users = User.query.filter_by(is_admin=False).order_by(User.id.desc()).all()
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    recent_users = User.query.filter(
        User.is_admin == False,
        User.created_at >= recent_cutoff
    ).count()

    return render_template('admin.html', users=all_users, recent_users=recent_users)

@admin_bp.route('/admin/export_users_csv')
@login_required
def export_users_csv():
    user = get_current_user()
    if not user or not user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('admin.admin_login'))

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Username', 'Email', 'Phone', 'Date Joined', 'Last Login'])

    users = User.query.filter_by(is_admin=False).all()
    for u in users:
        cw.writerow([
            u.id, u.username, u.email or '', u.phone or 'Not provided',
            u.created_at.strftime('%Y-%m-%d %H:%M:%S') if u.created_at else 'N/A',
            'Never'  # last_login field doesn't exist in current model
        ])

    output = si.getvalue()
    si.close()
    filename = f'users_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    resp = make_response(output)
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return resp

@admin_bp.route('/admin/export_portfolios_csv')
@login_required
def export_portfolios_csv():
    user = get_current_user()
    if not user or not user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('admin.admin_login'))

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow([
        'User ID', 'Username', 'Full Name', 'Company Name', 'Job Title',
        'Email', 'Phone', 'Skills', 'LinkedIn URL', 'GitHub URL',
        'Twitter URL', 'Project 1', 'Project 2', 'Project 3'
    ])

    portfolios = (db.session.query(Portfolio, User)
                 .join(User)
                 .filter(User.is_admin == False)
                 .all())

    for portfolio, u in portfolios:
        try:
            skills = ', '.join(json.loads(portfolio.skills)) if portfolio.skills else ''
        except Exception:
            skills = portfolio.skills or ''
        
        # Build contact info from individual fields
        contact_info = {
            'linkedin_url': portfolio.linkedin_url or '',
            'github_url': portfolio.github_url or '',
            'twitter_url': portfolio.twitter_url or ''
        }
            
        # Build projects from individual fields
        projects = {
            'project1': {
                'title': portfolio.project1_title or '',
                'description': portfolio.project1_desc or ''
            },
            'project2': {
                'title': portfolio.project2_title or '',
                'description': portfolio.project2_desc or ''
            },
            'project3': {
                'title': portfolio.project3_title or '',
                'description': portfolio.project3_desc or ''
            }
        }
        
        cw.writerow([
            u.id, u.username, portfolio.full_name or '', portfolio.company_name or '',
            portfolio.job_title or '', portfolio.email or '', portfolio.phone or '', skills,
            contact_info.get('linkedin_url', ''), contact_info.get('github_url', ''), 
            contact_info.get('twitter_url', ''),
            f"{projects.get('project1', {}).get('title', '')}: {projects.get('project1', {}).get('description', '')}",
            f"{projects.get('project2', {}).get('title', '')}: {projects.get('project2', {}).get('description', '')}",
            f"{projects.get('project3', {}).get('title', '')}: {projects.get('project3', {}).get('description', '')}"
        ])

    output = si.getvalue()
    si.close()
    filename = f'portfolios_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    resp = make_response(output)
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return resp


@admin_bp.route('/admin/delete-user/<username>', methods=['DELETE'])
@login_required
def delete_user(username):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.filter_by(username=username).first()
    if user:
        # Delete associated portfolio first
        portfolio = Portfolio.query.filter_by(user_id=user.id).first()
        if portfolio:
            db.session.delete(portfolio)
        
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'User not found'}), 404


@admin_bp.route('/admin/create-admin', methods=['GET', 'POST'])
@login_required
def create_admin():
    """Create a new admin user"""
    user = get_current_user()
    if not user or not user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('admin.admin_login'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip()
        
        if not username or not password or not email:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.create_admin'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.create_admin'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.create_admin'))
        
        from werkzeug.security import generate_password_hash
        new_admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=True
        )
        
        try:
            db.session.add(new_admin)
            db.session.commit()
            flash(f'Admin user "{username}" created successfully.', 'success')
            return redirect(url_for('admin.admin'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating admin user: {str(e)}', 'danger')
    
    return render_template('create_admin.html')


@admin_bp.route('/admin/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    """Delete multiple users"""
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user_ids = request.json.get('user_ids', [])
    if not user_ids:
        return jsonify({'error': 'No users selected'}), 400
    
    try:
        # Delete portfolios first
        Portfolio.query.filter(Portfolio.user_id.in_(user_ids)).delete(synchronize_session=False)
        # Delete users
        User.query.filter(User.id.in_(user_ids), User.is_admin == False).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'success': True, 'deleted_count': len(user_ids)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/admin/analytics')
@login_required
def analytics():
    """Get analytics data"""
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # User statistics
    total_users = User.query.filter_by(is_admin=False).count()
    users_with_portfolios = db.session.query(User).join(Portfolio).filter(User.is_admin == False).count()
    users_without_portfolios = total_users - users_with_portfolios
    
    # Recent registrations (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_registrations = User.query.filter(
        User.is_admin == False,
        User.created_at >= thirty_days_ago
    ).count()
    
    # Template usage
    template_usage = db.session.query(
        Portfolio.template_id,
        db.func.count(Portfolio.template_id)
    ).group_by(Portfolio.template_id).all()
    
    return jsonify({
        'total_users': total_users,
        'users_with_portfolios': users_with_portfolios,
        'users_without_portfolios': users_without_portfolios,
        'recent_registrations': recent_registrations,
        'template_usage': dict(template_usage)
    })


@admin_bp.route('/admin/user-details/<username>')
@login_required
def user_details(username):
    """Get detailed user information"""
    admin_user = get_current_user()
    if not admin_user or not admin_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'phone': user.phone,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'is_admin': user.is_admin,
        'portfolio': None
    }
    
    if user.portfolio:
        portfolio = user.portfolio
        user_data['portfolio'] = {
            'template_id': portfolio.template_id,
            'full_name': portfolio.full_name,
            'company_name': portfolio.company_name,
            'job_title': portfolio.job_title,
            'bio': portfolio.bio,
            'profile_pic': portfolio.profile_pic,
            'resume_file': portfolio.resume_file,
            'email': portfolio.email,
            'phone': portfolio.phone,
            'linkedin_url': portfolio.linkedin_url,
            'github_url': portfolio.github_url,
            'twitter_url': portfolio.twitter_url,
            'skills': json.loads(portfolio.skills) if portfolio.skills else [],
            'contact_info': {
                'email': portfolio.email,
                'phone': portfolio.phone,
                'linkedin_url': portfolio.linkedin_url,
                'github_url': portfolio.github_url,
                'twitter_url': portfolio.twitter_url
            },
            'projects': {
                'project1': {
                    'title': portfolio.project1_title,
                    'desc': portfolio.project1_desc,
                    'link': portfolio.project1_link
                },
                'project2': {
                    'title': portfolio.project2_title,
                    'desc': portfolio.project2_desc,
                    'link': portfolio.project2_link
                },
                'project3': {
                    'title': portfolio.project3_title,
                    'desc': portfolio.project3_desc,
                    'link': portfolio.project3_link
                }
            },
            'created_at': portfolio.created_at.isoformat() if portfolio.created_at else None,
            'updated_at': portfolio.updated_at.isoformat() if portfolio.updated_at else None
        }
    
    return jsonify(user_data)

@admin_bp.route('/admin/site-settings', methods=['GET', 'POST'])
def site_settings():
    """Manage site-wide settings including copyright and footer"""
    if 'user_id' not in session:
        flash('Please log in to access admin area.', 'error')
        return redirect(url_for('admin.admin_login'))
    
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('admin.admin_login'))
    
    # Get or create site settings
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings(
            company_name='InfySkills',
            copyright_year='2025',
            copyright_text='© 2025 InfySkills. All rights reserved.',
            footer_text='Powered by InfySkills Portfolio Builder'
        )
        db.session.add(settings)
        db.session.commit()
    
    if request.method == 'POST':
        try:
            # Update settings from form
            settings.company_name = request.form.get('company_name', 'InfySkills')
            settings.copyright_year = request.form.get('copyright_year', '2025')
            settings.copyright_text = request.form.get('copyright_text', '© 2025 InfySkills. All rights reserved.')
            settings.footer_text = request.form.get('footer_text', 'Powered by InfySkills Portfolio Builder')
            
            db.session.commit()
            flash('Site settings updated successfully!', 'success')
            return redirect(url_for('admin.site_settings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating settings: {str(e)}', 'error')
    
    return render_template('admin_site_settings.html', settings=settings)

@admin_bp.route('/admin/api/site-settings')
def api_site_settings():
    """API endpoint to get site settings"""
    settings = SiteSettings.query.first()
    if settings:
        return jsonify({
            'company_name': settings.company_name,
            'copyright_year': settings.copyright_year,
            'copyright_text': settings.copyright_text,
            'footer_text': settings.footer_text
        })
    else:
        return jsonify({
            'company_name': 'InfySkills',
            'copyright_year': '2025',
            'copyright_text': '© 2025 InfySkills. All rights reserved.',
            'footer_text': 'Powered by InfySkills Portfolio Builder'
        })