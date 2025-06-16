# config.py

import os
from dotenv import load_dotenv
import urllib

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with common settings."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-default-secret-key-for-dev')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TASK_SECRET_KEY = os.getenv('TASK_SECRET_KEY')
    AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

class DevelopmentConfig(Config):
    """Configuration for local development."""
    DEBUG = True
    
    # --- Database Configuration from .env ---
    db_server = os.getenv('DB_SERVER')
    db_name = os.getenv('DB_NAME')
    db_admin_login = os.getenv('DB_ADMIN_LOGIN')
    db_admin_password = os.getenv('DB_ADMIN_PASSWORD')
    
    def __init__(self):
        super().__init__() # It's good practice to call the parent's init
        # Now, check for the variables only when an instance is created
        if not all([os.getenv('DB_USER'), os.getenv('DB_PASSWORD'), os.getenv('DB_HOST'), os.getenv('DB_NAME')]):
            raise ValueError("One or more DB environment variables are not set for development.")
    
    password_safe = urllib.parse.quote_plus(db_admin_password)
    driver_name = 'ODBC Driver 18 for SQL Server'
    
    SQLALCHEMY_DATABASE_URI = (
        f"mssql+pyodbc://{db_admin_login}:{password_safe}@{db_server}/{db_name}?"
        f"driver={urllib.parse.quote_plus(driver_name)}"
        f"&TrustServerCertificate=yes"
    )

class TestingConfig(Config):
    """Configuration for testing."""
    TESTING = True
    WTF_CSRF_ENABLED = False  # Disable CSRF forms in tests for convenience
    # Use a fast, in-memory SQLite database for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Use a simpler password hasher in tests for speed
    BCRYPT_LOG_ROUNDS = 4

# You could also add a ProductionConfig class here for production settings
# class ProductionConfig(Config):
#     ...

# Dictionary to map string names to config classes
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    # 'production': ProductionConfig
}