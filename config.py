# Corporate Transaction Ledger System - Configuration File

import os
from datetime import timedelta

# Database Configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'password'),
    'database': os.environ.get('DB_NAME', 'ledger_db')
}

# Flask Configuration
class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging
    LOG_FILE = 'ledger.log'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = 'INFO'
    
    # Application Settings
    ITEMS_PER_PAGE = 25
    MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXPORT_FORMATS = ['csv', 'json', 'pdf']
    
    # Blockchain Settings
    HASH_ALGORITHM = 'sha256'
    BLOCK_VERIFICATION_ENABLED = True
    
    # Security Settings
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_SPECIAL = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_UPPERCASE = True
    
    # Feature Flags
    ENABLE_API = True
    ENABLE_REPORTS = True
    ENABLE_AUDIT_LOG = True
    ENABLE_EXPORT = True
    ENABLE_ROLE_BASED_ACCESS = True


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SECRET_KEY = 'dev-secret-key'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-must-be-set')


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'password',
        'database': 'ledger_db_test'
    }


# Select configuration based on environment
ENV = os.environ.get('FLASK_ENV', 'development')
if ENV == 'production':
    config = ProductionConfig
elif ENV == 'testing':
    config = TestingConfig
else:
    config = DevelopmentConfig


# User Roles
USER_ROLES = {
    'admin': {
        'permissions': ['create', 'read', 'export', 'manage_users', 'view_audit_log'],
        'description': 'Administrator - Full access'
    },
    'manager': {
        'permissions': ['create', 'read', 'export', 'view_audit_log'],
        'description': 'Manager - Can create and view transactions'
    },
    'user': {
        'permissions': ['create', 'read'],
        'description': 'User - Can create and view own transactions'
    },
    'viewer': {
        'permissions': ['read'],
        'description': 'Viewer - Read-only access'
    }
}

# Transaction Status Options
TRANSACTION_STATUS = {
    'pending': 'Pending',
    'success': 'Successful',
    'failed': 'Failed',
    'cancelled': 'Cancelled',
    'on_hold': 'On Hold'
}

# Report Types
REPORT_TYPES = {
    'daily_summary': 'Daily Summary Report',
    'weekly_summary': 'Weekly Summary Report',
    'monthly_summary': 'Monthly Summary Report',
    'transaction_detail': 'Transaction Detail Report',
    'account_wise': 'Account-wise Report',
    'status_wise': 'Status-wise Report'
}