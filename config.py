"""
Configuration Settings for LearnNova Application
"""

import os
from datetime import timedelta


class Config:
    """Base Configuration"""
    
    # Secret key for sessions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database - use absolute path for instance folder
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(BASE_DIR, "instance", "learnnova.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp4', 'webm'}
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CORS configuration
    CORS_HEADERS = 'Content-Type'
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5000']
    
    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'Asia/Kolkata'
    CELERY_ENABLE_UTC = True
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@learnnova.com'
    
    # Pagination
    ITEMS_PER_PAGE = 12
    API_ITEMS_PER_PAGE = 20
    
    # AI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    AI_MODEL = os.environ.get('AI_MODEL', 'gpt-3.5-turbo')
    
    # Payment Configuration
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/app.log'
    ERROR_LOG_FILE = 'logs/error.log'
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100 per day"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Recommendation System
    RECOMMENDATION_CACHE_TTL = int(os.environ.get('RECOMMENDATION_CACHE_TTL', 3600))
    RECOMMENDATION_MODEL_RETRAIN_INTERVAL = int(os.environ.get('RECOMMENDATION_MODEL_RETRAIN_INTERVAL', 86400))
    RECOMMENDATION_MIN_ENROLLMENTS = int(os.environ.get('RECOMMENDATION_MIN_ENROLLMENTS', 10))
    RECOMMENDATION_HYBRID_CF_WEIGHT = float(os.environ.get('RECOMMENDATION_HYBRID_CF_WEIGHT', 0.7))
    RECOMMENDATION_HYBRID_KW_WEIGHT = float(os.environ.get('RECOMMENDATION_HYBRID_KW_WEIGHT', 0.3))
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')


class DevelopmentConfig(Config):
    """Development Configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production Configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost/learnnova'


class TestingConfig(Config):
    """Testing Configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    WTF_CSRF_ENABLED = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
