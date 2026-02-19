# manage.py
import os
import subprocess
import sys

import click
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm.mapper import configure_mappers

from geo_uploader import create_app
from geo_uploader.extensions import db
from geo_uploader.models import Users, ADMIN, USER

# Create single application instance for CLI
application = create_app()


def check_port_in_use(port, show_error):
    """Check if the specified port is already in use."""
    try:
        result = subprocess.run(
            ["lsof", "-P", "-n", "-i", f":{port}"],
            capture_output=True,
            text=True,
        )
        if "LISTEN" in result.stdout:
            if show_error:
                print(
                    f"Error: Port {port} is already in use. Another server might be running."
                )
                print(result.stdout)
            # Parse the output to get process information
            processes = []
            for line in result.stdout.strip().split("\n")[1:]:  # Skip header line
                if "LISTEN" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        processes.append({"pid": parts[1], "command": parts[0]})
            return True, processes
    except FileNotFoundError:
        print(
            "Error: 'lsof' command not found. Please ensure it is installed and available in your PATH."
        )
        sys.exit(1)
    return False, []


@application.cli.command("start-local-foreground")
@click.option("--port", default=None, help="Server port")
def start_server_foreground(port):
    """Start the development server with development configuration."""
    if port is None:
        port = get_default_port(
            "SERVER_PORT", "Example: SERVER_PORT=5000 in .flaskenv"
        )

    port_in_use, _ = check_port_in_use(port, True)
    if port_in_use:
        return

    try:
        # Ensure the development folders exist
        # os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        # db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        # os.makedirs(os.path.dirname(db_path), exist_ok=True)

        import socket

        actual_hostname = socket.gethostname()
        application.logger.info(
            f"Running with {application.config.get('ENVIRONMENT')} configuration"
        )
        application.logger.info(
            f"Database: {application.config.get('SQLALCHEMY_DATABASE_URI')}"
        )
        application.logger.info(
            f"Upload folder: {application.config.get('UPLOAD_FOLDER')}"
        )

        # Start the Flask development server
        subprocess.run(["flask", "run", f"--port={port}"], check=True)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

@application.cli.command("start-local")
@click.option("--port", default=None, help="Server port")
def start_server(port):
    """Start the development server with development configuration."""
    if port is None:
        port = get_default_port(
            "SERVER_PORT", "Example: SERVER_PORT=5000 in .flaskenv"
        )

    port_in_use, _ = check_port_in_use(port, True)
    if port_in_use:
        return

    try:
        # Ensure the development folders exist
        # os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        # db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        # os.makedirs(os.path.dirname(db_path), exist_ok=True)

        import socket

        actual_hostname = socket.gethostname()

        application.logger.info(
            f"Running with {application.config.get('ENVIRONMENT')} configuration"
        )
        application.logger.info(
            f"Database: {application.config.get('SQLALCHEMY_DATABASE_URI')}"
        )
        application.logger.info(
            f"Upload folder: {application.config.get('UPLOAD_FOLDER')}"
        )

        # Start the Flask development server
        subprocess.run(
            [f"nohup flask run --port={port} > flask.log 2>&1 &"],
            shell=True,
            check=True,
        )

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

@application.cli.command("status")
def status():
    """Check the status of the server."""
    try:
        port = get_default_port(
            "SERVER_PORT", "Please set SERVER_PORT in .flaskenv"
        )
    except SystemExit:
        # get_default_port calls sys.exit(1) on error
        return

    running, processes = check_port_in_use(port, show_error=False)

    if running:
        print(f"Server (port {port}): RUNNING")
        print("  Process information:")
        for process in processes:
            print(f"  - PID: {process['pid']}, Command: {process['command']}")
    else:
        print(f"Server (port {port}): STOPPED")

@application.cli.command("init-db")
@click.option(
    "--env", default="development", help="Environment (development/production)"
)
def init_db(env):
    """Reset the database for the specified environment."""
    try:
        with application.app_context():
            db.drop_all()
            configure_mappers()
            db.create_all()

            admin = Users(name='Admin',
                          full_name='Admin',
                          email=u'admin@your-mail.com',
                          password=u'password')
            admin.role_code = ADMIN
            admin.verify_email()
            db.session.add(admin)

            for i in range(1, 2):
                user = Users(name=f'User{i}',
                             full_name=f'User{i}',
                             email=f'demo{i}@your-mail.com',
                             password=u'password',
                             role_code=USER)
                user.verify_email()
                db.session.add(user)


            db.session.commit()

            print("Database initialized with 3 users (Admin, password) and (User1, password), (User2, password)")

            print(f"Database initialization complete for {env} environment.")
    except Exception as e:
        print(f"An error occurred during database reset: {e}")
        sys.exit(1)


def get_default_port(env_var, fallback_message):
    """Get port from environment variable or show error message"""
    port = os.environ.get(env_var)
    if not port:
        print(f"Error: {env_var} environment variable is not set.")
        print(f"Please set {env_var} in your .flaskenv file.")
        print(fallback_message)
        sys.exit(1)

    try:
        return int(port)
    except ValueError:
        print(f"Error: {env_var} must be a valid integer, got: {port}")
        sys.exit(1)


if __name__ == "__main__":
    application.cli()
