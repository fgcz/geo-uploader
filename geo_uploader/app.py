import os

from flask import Flask

from geo_uploader.config import BaseConfig
from geo_uploader.extensions import (
    admin,
    cache,
    db,
    login_manager,
    mail,
    migrate,
)
from geo_uploader.models import Users, UsersAdmin
from geo_uploader.views import auth, geo, main, metadata, progress, upload

from .config import get_config

__all__ = ["create_app"]

DEFAULT_BLUEPRINTS = (main, auth, upload, metadata, progress, geo)


def create_app(app_name=None, blueprints=None):
    """Create a Flask app with the appropriate configuration."""

    if app_name is None:
        app_name = BaseConfig.PROJECT

    if blueprints is None:
        blueprints = DEFAULT_BLUEPRINTS

    # Get appropriate config
    active_config = get_config()

    app = Flask(
        app_name,
        instance_path=active_config.INSTANCE_FOLDER_PATH,
        instance_relative_config=True,
    )
    configure_app(app, active_config)

    # Full initialization
    configure_hook(app)
    configure_blueprints(app, blueprints)
    configure_extensions(app)
    configure_template_filters(app)
    configure_error_handlers(app)
    configure_logging(app)

    return app


def configure_app(app, config=None):
    app.config.from_object(BaseConfig)

    if config:
        app.config.from_object(config)

def configure_extensions(app):
    # flask-sqlalchemy
    db.init_app(app)

    # flask-migrate
    migrate.init_app(app, db)

    # flask-mail
    mail.init_app(app)

    # flask-cache
    cache.init_app(app)

    # flask-admin
    admin.add_view(UsersAdmin(db.session))
    admin.init_app(app)

    # flask-login
    @login_manager.user_loader
    def load_user(id):
        return Users.query.get(id)

    login_manager.setup_app(app)


def configure_blueprints(app, blueprints):
    # Configure blueprints in views

    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def configure_template_filters(app):
    @app.template_filter()
    def format_bytes(value):
        """Convert bytes to a human-readable format (KB, MB, GB, etc.)."""
        if value is None or not isinstance(value, int | float):
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(value)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.1f} {units[unit_index]}"

    @app.template_filter()
    def basename(value):
        """Convert bytes to a human-readable format (KB, MB, GB, etc.)."""
        basename = os.path.basename(value)

        return f"{basename}"


def configure_logging(app):
    # Configure logging

    import logging
    from logging.handlers import RotatingFileHandler

    # Ensure log folder exists
    log_folder = app.config.get("LOG_FOLDER", os.path.join(app.instance_path, "logs"))
    os.makedirs(log_folder, exist_ok=True)

    # Set log level based on config
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"))

    # Setup file handler
    log_file = os.path.join(log_folder, f"{app.config.get('ENVIRONMENT')}.log")
    handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=10)
    handler.setLevel(log_level)

    # Set formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add to app
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)


def configure_hook(app):
    @app.before_request
    def before_request():
        pass


def configure_error_handlers(app):
    @app.errorhandler(403)
    def forbidden_page(error):
        return "Oops! You don't have permission to access this page.", 403

    @app.errorhandler(404)
    def page_not_found(error):
        return "Opps! Page not found.", 404

    @app.errorhandler(500)
    def server_error_page(error):
        return "Oops! Internal server error. Please try after sometime.", 500
