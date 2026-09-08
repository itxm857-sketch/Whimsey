import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-change-me')
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR / "whimsy.db"}')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', '0') == '1'
    SESSION_TYPE = 'sqlalchemy'
    SESSION_SQLALCHEMY_TABLE = 'flask_sessions'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'product-images')
    UPLOAD_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
    SHIPPING_FEE = int(os.getenv('SHIPPING_FEE', '300'))
    LOW_STOCK_DEFAULT = int(os.getenv('LOW_STOCK_DEFAULT', '5'))
    ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', '12'))
    ADMIN_ITEMS_PER_PAGE = int(os.getenv('ADMIN_ITEMS_PER_PAGE', '20'))
