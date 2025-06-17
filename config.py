# config.py

import os
from dotenv import load_dotenv
import urllib

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class with common settings."""

    SECRET_KEY = os.getenv("SECRET_KEY", "a-default-secret-key-for-dev")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TASK_SECRET_KEY = os.getenv("TASK_SECRET_KEY")
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


class DevelopmentConfig(Config):
    # It's fine to have static config values here, but NOT logic that uses os.getenv()
    DEBUG = True

    # def __init__(self):
    #     super().__init__()

    #     # MOVE ALL ENVIRONMENT-DEPENDENT LOGIC INSIDE __init__
    #     db_user = os.getenv('DB_USER')
    #     db_password = os.getenv('DB_PASSWORD')
    #     db_host = os.getenv('DB_HOST')
    #     db_name = os.getenv('DB_NAME')

    #     # First, check if the variables exist
    #     if not all([db_user, db_password, db_host, db_name]):
    #         raise ValueError("One or more DB environment variables are not set for development.")

    #     # Now, perform the parsing and construct the URI
    #     password_safe = urllib.parse.quote_plus(db_password)
    #     self.SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc://{db_user}:{password_safe}@{db_host}:1433/{db_name}?driver=ODBC+Driver+17+for+SQL+Server"


class TestingConfig(Config):
    """Configuration for testing."""

    TESTING = True
    WTF_CSRF_ENABLED = False  # Disable CSRF forms in tests for convenience
    # Use a fast, in-memory SQLite database for tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # Use a simpler password hasher in tests for speed
    BCRYPT_LOG_ROUNDS = 4


# You could also add a ProductionConfig class here for production settings
# class ProductionConfig(Config):
#     ...

# Dictionary to map string names to config classes
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    # 'production': ProductionConfig
}
