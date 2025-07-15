FLASK_ENV=production
FLASK_DEBUG=1
FLASK_APP=manage.py

SERVER_HOST=localhost
SERVER_PORT_PROD=8000
SERVER_PORT_DEV=8001

# =============================================================================
# COMPLETE THIS
# =============================================================================
# staring from base folder, how many levels of subfolders to recursively show
MAX_FOLDER_SELECTION_DEPTH=10

# NOTICE
# This is the base path from where the file selector lets you choose your raw data
# If you mistype this root path, or want to change it, just update this path
# and relaunch the server, no need re-installing anything
BASE_FOLDER_SELECTION=/Users/user/Desktop

# =============================================================================
# DATA DIRECTORIES (OPTIONAL)
# =============================================================================
# By default, data is stored in 'geo_uploader_data' next to the source code
# Uncomment and set this to use a custom location
# GEO_UPLOADER_DATA_ROOT=/User/user/SomeOtherPath
# SQLAlchemy database URI (optional - defaults to SQLite in data directory)
# SQLALCHEMY_DATABASE_URI_PROD=sqlite:///path/to/prod.db
# SQLALCHEMY_DATABASE_URI_DEV=sqlite:///path/to/dev.db

# =============================================================================
# EXTERNAL DEPENDENCIES
# =============================================================================

GEO_SERVER=ftp-private.ncbi.nlm.nih.gov
GEO_USERNAME=geoftp

CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=60

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
# MAIL_USERNAME defined in .env
# MAIL_PASSOWRD defined in .env
MAIL_USE_TLS=true
MAIL_DEBUG=false
