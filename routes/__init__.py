# routes/__init__.py
from .auth import auth_bp
from .portfolio import portfolio_bp
from .admin import admin_bp

# Import all blueprints
__all__ = ['auth_bp', 'portfolio_bp', 'admin_bp']