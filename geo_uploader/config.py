import os
from typing import Type
from dotenv import load_dotenv

load_dotenv(".flaskenv")
load_dotenv()  # This loads the .env file


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


def get_required_env(key: str, convert_type: Type[str] | Type[bool] | Type[int] = str):
    """Get required environment variable or raise ConfigError."""
    value = os.environ.get(key)
    if value is None:
        raise ConfigError(
            f"Required environment variable (.flaskenv) '{key}' is not set"
        )

    if convert_type is bool:
        return value.lower() in ("true", "1", "yes", "on")
    elif convert_type is int:
        try:
            return int(value)
        except ValueError:
            raise ConfigError(
                f"Environment variable '{key}' must be a valid integer, got: {value}"
            )

    return convert_type(value)


class BaseConfig:
    PROJECT = "geo_uploader"
    PROJECT_NAME = "geo_uploader.domain"
    PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    DEBUG = False
    TESTING = False
    LOG_LEVEL = "INFO"
    SECRET_KEY = get_required_env("SECRET_KEY")
    SERVER_HOST = get_required_env("SERVER_HOST")

    PARENT_DIR = os.path.dirname(PROJECT_ROOT)
    DEFAULT_DATA_ROOT = os.path.join(PARENT_DIR, "geo_uploader_data")
    DATA_ROOT = os.environ.get("GEO_UPLOADER_DATA_ROOT", DEFAULT_DATA_ROOT)
    INSTANCE_FOLDER_PATH = os.path.join(DATA_ROOT, "instance")

    UPLOAD_FOLDER = os.path.join(DATA_ROOT, "uploads")
    LOG_FOLDER = os.path.join(DATA_ROOT, "logs")
    DATABASE_PATH = os.path.join(DATA_ROOT, "database")
    BACKUP_PATH = os.path.join(DATA_ROOT, "backups")
    JOB_PATH = os.path.join(DATA_ROOT, "jobs")

    BASE_EXCEL = os.path.join(PROJECT_ROOT, "geo_uploader/utils/metadata/seq_template.xlsx")

    GEO_SERVER = get_required_env("GEO_SERVER")
    GEO_USERNAME = get_required_env("GEO_USERNAME")

    MAIL_DEBUG = get_required_env("MAIL_DEBUG", bool)
    MAIL_SERVER = get_required_env("MAIL_SERVER")
    MAIL_PORT = get_required_env("MAIL_PORT", int)
    MAIL_USE_TLS = get_required_env("MAIL_USE_TLS", bool)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", 'a')
    MAIL_PASSWORD = os.getenv("MAIL_APP_PASSWORD", 'aa')
    MAIL_DEFAULT_SENDER = MAIL_USERNAME

    SESSION_TYPE = "cache"
    CACHE_TYPE = get_required_env("CACHE_TYPE")
    CACHE_DEFAULT_TIMEOUT = get_required_env("CACHE_DEFAULT_TIMEOUT", int)

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_FOLDER_SELECTION_DEPTH = get_required_env("MAX_FOLDER_SELECTION_DEPTH", int)
    BASE_FOLDER_SELECTION_PATH = get_required_env("BASE_FOLDER_SELECTION")


    @classmethod
    def create_directories(cls):
        """Create required directories if they don't exist"""
        dirs_to_create = [
            cls.DATA_ROOT,
            cls.UPLOAD_FOLDER,
            cls.LOG_FOLDER,
            cls.DATABASE_PATH,
        ]

        for directory in dirs_to_create:
            os.makedirs(directory, exist_ok=True)


class ProductionConfig(BaseConfig):
    ENVIRONMENT = "production"
    DEBUG = False
    LOG_LEVEL = "INFO"

    SERVER_PORT = get_required_env("SERVER_PORT_PROD", int)
    SERVER_URL = f"http://{BaseConfig.SERVER_HOST}:{SERVER_PORT}"

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI",
        default=f"sqlite:///{os.path.join(BaseConfig.DATABASE_PATH, 'prod.db')}"
    )


class DevelopmentConfig(BaseConfig):
    ENVIRONMENT = "development"
    DEBUG = True
    LOG_LEVEL = "DEBUG"

    SERVER_PORT = os.getenv("SERVER_PORT_DEV")
    SERVER_URL = f"http://{BaseConfig.SERVER_HOST}:{SERVER_PORT}"

    DEFAULT_DATA_ROOT = os.path.join(BaseConfig.PARENT_DIR, "geo_uploader_dev_data")
    DATA_ROOT = os.environ.get("GEO_UPLOADER_DATA_ROOT", DEFAULT_DATA_ROOT)

    UPLOAD_FOLDER = os.path.join(DATA_ROOT, "uploads")
    LOG_FOLDER = os.path.join(DATA_ROOT, "logs")
    DATABASE_PATH = os.path.join(DATA_ROOT, "database")
    BACKUP_PATH = os.path.join(DATA_ROOT, "backups")
    INSTANCE_FOLDER_PATH = os.path.join(DATA_ROOT, "instance")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI_DEV",
        default=f"sqlite:///{os.path.join(DATABASE_PATH, 'dev.db')}"
    )


def validate_email_config():
    """Validate that email configuration is properly set up."""
    mail_username = os.environ.get("MAIL_USERNAME", "").strip()
    mail_password = os.environ.get("MAIL_APP_PASSWORD", "").strip()

    if not mail_username or not mail_password:
        error_msg = """
╔════════════════════════════════════════════════════════════════════════════════╗
║                           EMAIL CONFIGURATION REQUIRED                         ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║  The application requires email configuration to send verification emails      ║
║  and notifications. Please configure the following in your .env file:          ║
║                                                                                ║
║  MAIL_USERNAME=your_email@gmail.com                                            ║
║  MAIL_APP_PASSWORD=your_app_password                                           ║
║                                                                                ║
║  For Gmail users:                                                              ║
║  1. Enable 2-Factor Authentication                                             ║
║  2. Generate an "App Password" (not your regular password)                     ║
║  3. Use the App Password as MAIL_APP_PASSWORD                                  ║
║                                                                                ║
║  Missing configuration:                                                        ║
"""

        missing = []
        if not mail_username:
            missing.append("║  - MAIL_USERNAME is not set")
        if not mail_password:
            missing.append("║  - MAIL_APP_PASSWORD is not set")

        error_msg += "\n".join(missing)
        error_msg += """
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""
        raise ConfigError(error_msg)


# Dictionary mapping for easy access to different configurations
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


# Function to get the appropriate config based on environment
def get_config():
    flask_env = os.environ.get("FLASK_ENV", "development")
    # validate_email_config()
    config_class = config_by_name.get(flask_env, config_by_name["default"])
    config_class.create_directories()
    return config_class

