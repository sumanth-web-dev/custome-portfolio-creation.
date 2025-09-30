import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# --- App Initialization & Config ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio_builder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# Session validation middleware
@app.before_request
def validate_session():
    if 'user_id' in session:
        # Check if the user exists
        user = User.query.get(session['user_id'])
        if not user:
            # Clear invalid session
            session.clear()
        # Update session timestamp
        session['last_active'] = str(datetime.now())
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

db = SQLAlchemy(app)

# Add a Jinja filter to parse JSON strings in templates
@app.template_filter('fromjson')
def fromjson_filter(value):
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

# --- Database Models ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    portfolio = db.relationship('Portfolio', backref='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    template_id = db.Column(db.Integer, nullable=False, default=1)
    
    # Personal Info
    full_name = db.Column(db.String(100), default='Your Name')
    company_name = db.Column(db.String(100), default='Your Company')
    job_title = db.Column(db.String(100), default='Your Job Title')
    bio = db.Column(db.Text, default='A little bit about yourself.')
    profile_pic = db.Column(db.String(200), default='/static/images/default_avatar.png')
    resume_file = db.Column(db.String(200), default='#')

    # Contact & Social
    email = db.Column(db.String(120), default='your.email@example.com')
    phone = db.Column(db.String(20), default='+1 234 567 890')
    linkedin_url = db.Column(db.String(200), default='#')
    github_url = db.Column(db.String(200), default='#')
    twitter_url = db.Column(db.String(200), default='#')

    # Skills (stored as JSON string)
    skills = db.Column(db.Text, default='["HTML", "CSS", "JavaScript"]')

    # Projects
    project1_title = db.Column(db.String(100), default='Project One')
    project1_desc = db.Column(db.Text, default='Description of your first project.')
    project1_link = db.Column(db.String(200), default='#')
    
    project2_title = db.Column(db.String(100), default='Project Two')
    project2_desc = db.Column(db.Text, default='Description of your second project.')
    project2_link = db.Column(db.String(200), default='#')

    project3_title = db.Column(db.String(100), default='Project Three')
    project3_desc = db.Column(db.Text, default='Description of your third project.')
    project3_link = db.Column(db.String(200), default='#')


# --- Helper Functions ---
def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Main Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('index'))
    return render_template('dashboard.html', user=user, portfolio=user.portfolio)

# --- Admin Routes ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.is_admin and user.check_password(password):
            session['user_id'] = user.id
            flash('Admin login successful.', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid admin credentials.', 'danger')
            return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

@app.route('/admin')
def admin():
    user = get_current_user()
    if not user or not user.is_admin:
        return redirect(url_for('admin_login'))
    
    all_users = User.query.filter_by(is_admin=False).all()
    return render_template('admin.html', users=all_users)

# --- User & Auth Routes ---

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('index'))

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    
    # Create a default portfolio for the new user
    new_portfolio = Portfolio(user=new_user)
    db.session.add(new_portfolio)
    
    db.session.commit()

    flash('Registration successful! Please log in.', 'success')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        # Make the session permanent but with configured lifetime
        session.permanent = True
        session['user_id'] = user.id
        session['logged_in_time'] = str(datetime.now())
        
        if user.is_admin:
            return redirect(url_for('admin'))
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password.', 'danger')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# --- Portfolio & API Routes ---

@app.route('/<username>')
def view_portfolio(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not user.portfolio:
        return "This user hasn't set up their portfolio yet.", 404
        
    template_file = f"/portfolio/{user.portfolio.template_id}.html"
    return render_template(template_file, p=user.portfolio)

@app.route('/preview', methods=['POST'])
def preview():
    # Get user and check authentication
    user = get_current_user()
    if not user:
        return jsonify({
            'success': False, 
            'message': 'Authentication required. Please log in again.',
            'user_id': session.get('user_id'),
            'session_data': dict(session)
        }), 403
    
    # Get and validate the request data
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
        if skills and isinstance(skills, str):
            try:
                json.loads(skills)  # Validate JSON format
            except json.JSONDecodeError:
                cleaned_data['skills'] = '[]'
        else:
            cleaned_data['skills'] = '[]'
            
        # Create a temporary portfolio object for preview
        preview_portfolio = Portfolio(**cleaned_data)
        template_file = f"/portfolio/{template_id}.html"
        return render_template(template_file, p=preview_portfolio)
        
    except json.JSONDecodeError as e:
        return jsonify({'success': False, 'message': f'Invalid JSON data: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating preview: {str(e)}'}), 400
    
    try:
        # Handle skills data
        skills = cleaned_data.get('skills')
        if skills and isinstance(skills, str):
            try:
                # Validate JSON format
                json.loads(skills)
            except json.JSONDecodeError:
                cleaned_data['skills'] = '[]'
        else:
            cleaned_data['skills'] = '[]'

        # Create a temporary portfolio object for preview
        preview_portfolio = Portfolio(**cleaned_data)
        template_file = f"/portfolio/{template_id}.html"
        return render_template(template_file, p=preview_portfolio)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating preview: {str(e)}'}), 400

@app.route('/save_portfolio', methods=['POST'])
def save_portfolio():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 403
    
    data = request.get_json()
    
    portfolio = user.portfolio
    if not portfolio:
        portfolio = Portfolio(user_id=user.id)
        db.session.add(portfolio)

    # Update portfolio fields from the received JSON data
    for key, value in data.items():
        if hasattr(portfolio, key):
            setattr(portfolio, key, value)
            
    db.session.commit()
    return jsonify({'success': True, 'message': 'Portfolio saved successfully!'})

@app.route('/upload', methods=['POST'])
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
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        # Return the URL path, not the filesystem path
        url_path = f"/{filepath.replace(os.path.sep, '/')}"
        return jsonify({'success': True, 'filepath': url_path})

    return jsonify({'success': False, 'message': 'File type not allowed'}), 400


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create upload folder if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        # Create a default admin user if one doesn't exist
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', is_admin=True)
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created with username 'admin' and password 'admin123'")
    app.run(debug=True)

