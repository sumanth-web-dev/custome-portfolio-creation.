# config.py (BETTER FIX)
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///portfolio_builder.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
    
    # Sessions
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Domain and security
    DOMAIN_URL = os.environ.get('DOMAIN_URL', 'http://localhost:8000').rstrip('/')
    PREFERRED_URL_SCHEME = 'https'
    
    # Environment
    ENV = os.environ.get('ENV', 'development').lower()
    SESSION_COOKIE_SECURE = (ENV == 'production')
    
    # SMTP Configuration
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    SMTP_FROM = os.environ.get('SMTP_FROM', 'no-reply@example.com')
    
    # SSL configuration
    SSL_CERT_PATH = os.environ.get('SSL_CERT_PATH')
    SSL_KEY_PATH = os.environ.get('SSL_KEY_PATH')
    
    # Allowed hosts - FIXED: Regular attribute with method to get values
    def get_allowed_hosts(self):
        allowed_hosts_env = os.environ.get('ALLOWED_HOSTS')
        if allowed_hosts_env:
            return [h.strip() for h in allowed_hosts_env.split(',')]
        else:
            domain = self.DOMAIN_URL.replace('https://', '').replace('http://', '')
            return [domain, 'localhost', '127.0.0.1']

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    def get_allowed_hosts(self):
        return ['localhost', '127.0.0.1', '0.0.0.0', '*']

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}