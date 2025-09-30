# app.py
import os
import json
from dotenv import load_dotenv
from flask import Flask, render_template
import json

# Load environment variables
load_dotenv()

from config import config
from models import db
from utils.helpers import validate_session
from routes.auth import auth_bp
from routes.portfolio import portfolio_bp
from routes.admin import admin_bp
from routes.email import email_bp

from extensions import login_manager


def create_app(config_name=None):
    # Create Flask app
    app = Flask(__name__)
    
    # Determine configuration
    if config_name is None:
        config_name = os.environ.get('ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)

     # Initialize extensions with app
    login_manager.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Add a Jinja filter to parse JSON strings in templates
    @app.template_filter('fromjson')
    def fromjson_filter(value):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    # Import models within the app context to avoid circular imports
    with app.app_context():
        from models import User
        
        @login_manager.user_loader
        def load_user(user_id):
            """Load user by ID for Flask-Login"""
            return User.query.get(int(user_id))


    
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(email_bp)
    


    # Add template filter
    @app.template_filter('fromjson')
    def fromjson_filter(value):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    # Session validation middleware
    @app.before_request
    def before_request():
        validate_session()
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    return app

def init_db(app):
    """Initialize database and create default admin"""
    with app.app_context():
        db.create_all()
        # Create upload folder
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        # Create default admin user
        from models import User
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', is_admin=True, email = 'admin@example.com', phone= "1236547890")
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            app.logger.info("Admin user created: admin/admin123")

# app.py - Update the DomainMiddleware class
class DomainMiddleware:
    def __init__(self, wsgi_app, app):
        self.wsgi_app = wsgi_app
        self.flask_app = app

    def __call__(self, environ, start_response):
        # Check host against ALLOWED_HOSTS
        host = environ.get('HTTP_HOST', '').split(':')[0]
        
        # Use the method to get allowed hosts
        allowed_hosts = self.flask_app.config.get('ALLOWED_HOSTS', [])
        
        # If it's a property/method, call it to get the actual list
        if callable(allowed_hosts):
            allowed_hosts = allowed_hosts()
        
        # Allow localhost always in dev, or if no hosts specified
        if not allowed_hosts or host in allowed_hosts or host == 'localhost' or '*' in allowed_hosts:
            return self.wsgi_app(environ, start_response)

        start_response('400 Bad Request', [('Content-Type', 'text/plain')])
        return [b'Invalid host header']



if __name__ == '__main__':
    # Create application
    app = create_app()
    
    # Initialize database
    init_db(app)
    
    # Apply middleware
    app.wsgi_app = DomainMiddleware(app.wsgi_app, app)
    
    # Server configuration
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # SSL configuration
    ssl_context = None
    cert_path = app.config.get('SSL_CERT_PATH')
    key_path = app.config.get('SSL_KEY_PATH')
    if cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path):
        ssl_context = (cert_path, key_path)
        print(f"Running with SSL on {app.config['DOMAIN_URL']}")
    
    # Start server
    app.run(host=host, port=port, ssl_context=ssl_context, debug=debug)