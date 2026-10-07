"""
ClaimGuard Configuration Management
Handles database, storage, and environment-specific settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'claimguard-dev-secret'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'claimguard-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = 604800  # 7 days


class DevelopmentConfig(Config):
    """Development environment (SQLite for quick iteration)"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///claimguard.db'
    SQLALCHEMY_ECHO = True  # Log SQL queries
    
    # Local file storage for development
    STORAGE_TYPE = 'local'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')


class ProductionConfig(Config):
    """Production environment (PostgreSQL + S3)"""
    DEBUG = False
    
    # PostgreSQL production database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost:5432/claimguard'
    SQLALCHEMY_ECHO = False
    
    # AWS S3 storage for production
    STORAGE_TYPE = 's3'
    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_S3_REGION = os.environ.get('AWS_S3_REGION', 'us-east-1')


class TestingConfig(Config):
    """Testing environment (in-memory SQLite)"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    
    STORAGE_TYPE = 'local'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'test_uploads')


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
    }
    
    return configs.get(env, DevelopmentConfig)
