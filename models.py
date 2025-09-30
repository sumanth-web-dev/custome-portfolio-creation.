from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db  # Import from extensions

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), default='InfySkills')
    copyright_year = db.Column(db.String(10), default='2025')
    copyright_text = db.Column(db.String(200), default='© 2025 InfySkills. All rights reserved.')
    footer_text = db.Column(db.Text, default='Powered by InfySkills Portfolio Builder')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<SiteSettings {self.company_name}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationship with Portfolio
    portfolio = db.relationship('Portfolio', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    template_id = db.Column(db.Integer, default=1)
    
    # Personal Info
    full_name = db.Column(db.String(100), default='Your Name')
    company_name = db.Column(db.String(100), default='Your Company')
    job_title = db.Column(db.String(100), default='Your Job Title')
    bio = db.Column(db.Text, default='A little bit about yourself.')
    profile_pic = db.Column(db.String(200), default='/static/images/default_avatar.svg')
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
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<Portfolio for User {self.user_id}>'