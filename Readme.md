# GEO-Uploader

A Flask web application for streamlined genomic data uploads to the NCBI GEO repository with automated metadata generation.

## Table of Contents

- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [Trouble Shooting](#trouble-shooting)
- [Architecture Overview](#-architecture-overview)
- [Configuration](#-configuration)
- [Project Structure](#-project-structure)
- [Documentation Links](#-documentation-links)

## 🧬 Project Overview

GEO-Uploader simplifies the process of uploading bulk RNA and single-cell genomic datasets to the [NCBI GEO repository](https://www.ncbi.nlm.nih.gov/geo/). The application automates metadata sheet generation, handles file uploads via FTP, and provides a user-friendly interface for managing the entire submission workflow.

**Key Benefits:**
- Automated metadata.xlsx generation with MD5 checksums and file information
- Multiple data input methods (Sushi integration, folder selection, direct paths)
- Background job processing with monitoring capabilities
- User role management and administrative oversight

## 🚀 Quick Start

### Prerequisites
- Conda/Mamba package manager

### Installation

#### Using Makefile (suggested for Mac/Linux)
```bash
# File structure recommended
# GeoUploader/
# ├── geo-uploader/          # This repository
# └── geo_uploader_data/     # Auto-created
git clone https://gitlab.bfabric.org/Genomics/geo-uploader.git
cd geo-uploader
git checkout -f public

# Install environment and dependencies
make setup-env

# Setup configuration files
make setup-config
```

Update of the following configuration files
- `MAIL_USERNAME` (.env)
- `MAIL_APP_PASSWORD` (.env)
- `BASE_FOLDER_SELECTION` (.flaskenv)

```bash
nano .env      
nano .flaskenv 

# Initialize database
make setup-db
# Available logins are given by default
# (Admin, password)
# (User1, password)
# (User2, password)

# Start development server
conda activate gi_geo-uploader
flask status
flask start-prod
# Click on the links given or the terminal to access the server
# http://127.0.0.1:8000


# If you want to have your application run on the background
# flask start-prod-background
```
### Setup without Makefile (Suggested for Windows)
```bash
# File structure recommended
# GeoUploader/
# ├── geo-uploader/          # This repository
# └── geo_uploader_data/     # Auto-created

mkdir GeoUploader && cd GeoUploader
git clone https://gitlab.bfabric.org/Genomics/geo-uploader.git 
cd geo-uploader
git checkout -f public

# Create the conda environment from environment.yml
conda env create -f environment.yml || echo "Environment might already exist"
conda activate gi_geo-uploader
# Install the project in editable mode
pip install -e .

# Setup configuration files
# Copy default configuration file
cp .env.example .env
```

Update of the following configuration files
- `MAIL_USERNAME` (.env)
- `MAIL_APP_PASSWORD` (.env)
- `BASE_FOLDER_SELECTION` (.flaskenv)
 
```bash
# Edit required email configuration
# quit nano with Ctrl+X
nano .env  # Set MAIL_USERNAME, MAIL_APP_PASSWORD
nano .flaskenv # SET BASE_FOLDER_SELECTION

# Initialize database
flask init-db
# Available logins are given by default
# (Admin, password)
# (User1, password)
# (User2, password)

# Start development server
flask run -p 8000
# Click on the links given or the terminal to access the server
# http://127.0.0.1:8000

```

### Before First Use
Complete GEO registration following the [FGCZ GEO Upload Guide](https://fgcz-intranet.uzh.ch/tiki-index.php?page=web.seq.geo_upload).

### Example Upload
Once the server is up and running, and you can access it, you can try a mock upload.  
`/gstore/projects/raw_processed_paired` contains some data which is ready for testing.
![Upload Example Data](images/New%20Session%20Example.png)

## Trouble Shooting
- flask not recognized as a command
  - Make sure that the conda environment gi_geo-uploader is active, some terminals fail silently to activate it

- job failures
  - There can be many reasons, one common one is that the port on which the server is running is not the same as the port the jobs call
  - Make sure that running flask run -p 8000, this port is the same as the port specified in .flaskenv
  - For more debugging power, check the following paths
    - `geo_uploader_data/jobs/jobs.json`
    - `geo_uploader_data/uploads/UPLOAD_TITLE/jobs/upload_md5.out`
    

- Verification email not sent on new user registration
  - MAIL_USERNAME, MAIL_APP_PASSWORD are not set correctly in .env

- Google Account doesn't support AppPasswords
  - No immediate solution, try with different accounts or debug your google account

- Cannot find the folder you are looking for on a new submission
  - Update your BASE_PATH in .flaskenv, everything is shown relative to this
  - No need to re-install, just Ctrl+C and restart the server again

- Cannot install using Makefile
  - Use the alternative version without Makefile for Windows (documented above)

- `lsof` error on Windows when running `flask start-prod` or `flask status`
  - lsof is a command only for Mac/Linux, in a Windows computer use the alternative commands to start the server
  - `flask run`

## 🏗️ Architecture Overview

### System Components
- **Flask Monolith**: MVC architecture with service layer
- **Database**: SQLite with Alembic migrations
- **Job Processing**: Slurm scheduler with fallback to background processes
- **Authentication**: Flask-Login with LDAP integration (FGCZ)
- **Admin Interface**: Flask-Admin for user management and oversight
- **File Storage**: Local filesystem with configurable upload directories

### External Services
| Service | Purpose | Scope |
|---------|---------|-------|
| Sushi Database | Dataset integration | FGCZ only |
| LDAP | User authentication | FGCZ only |
| FTP | File uploads to GEO | All users |
| Slurm | Job scheduling | Server-dependent |
| Email Service | Notifications | All users |


## ⚙️ Configuration

### Environment Files
- **`.env`**: Sensitive configuration (database, API keys, passwords)
- **`.flaskenv`**: Flask-specific settings (debug mode, ports)
- **`config.py`**: Application configuration classes

### Configuration Classes (config.py)
- BaseConfig
- Development
- Production

## 📁 Project Structure

```
geo-uploader/
├── documentation/          # Hand-written documentation
├── geo_uploader/          # Main application package
│   ├── dto/              # Data transfer objects
│   ├── forms/            # WTForms form definitions
│   ├── models/           # SQLAlchemy database models
│   ├── services/         # Business logic layer
│   ├── views/            # Flask route controllers
│   ├── static/           # CSS, JavaScript, images
│   ├── templates/        # Jinja2 HTML templates
│   ├── utils/            # Helper functions for the upload script and utilities
│   └── config.py         # Application configuration
├── scripts/              # Cron job helpers
├── environment.yml       # Conda environment specification
├── pyproject.toml        # Python project configuration
├── Makefile             # Development commands
└── manage.py            # Flask CLI commands
```

## Maintainers
- **Primary Contact**: [ronald.domi@uzh.ch](mailto:ronald.domi@uzh.ch)
