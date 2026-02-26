# GEO-Uploader

A Flask web application for streamlined genomic data uploads to the NCBI GEO repository with automated metadata generation.

## FGCZ Geo Uploader (Guest Account)
https://geo-uploader.fgcz.uzh.ch/   

## Setup Video explanation
[▶ Watch the setup tutorial](https://fgcz.github.io/geo-uploader/documentation/tutorial_setup.html)

## Core Facility integration
[▶ Watch the integration tutorial](https://fgcz.github.io/geo-uploader/documentation/tutorial_integration.html)
  
## Table of Contents

- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [Trouble Shooting](#trouble-shooting)
- [Architecture Overview](#-architecture-overview)
- [Configuration](#-configuration)
- [Project Structure](#-project-structure)
- [Documentation Links](#-documentation-links)

## Project Overview

GEO-Uploader simplifies the process of uploading bulk RNA and single-cell genomic datasets to the [NCBI GEO repository](https://www.ncbi.nlm.nih.gov/geo/). The application automates metadata sheet generation, handles file uploads via FTP, and provides a user-friendly interface for managing the entire submission workflow.

**Key Benefits:**
- Automated metadata.xlsx generation with MD5 checksums and file information
- Multiple data input methods (Sushi integration, folder selection, direct paths)
- Background job processing with monitoring capabilities
- User role management and administrative oversight

## Quick Start
### Prerequisites
- Docker
- Docker Compose

### Installation
```bash
cd geo-uploader
```

Update docker-compose.yml  
Update the path to a root from where you can access all you data.   
```bash
volumes:
  # UPDATE THIS !!
  - /Users/user/Desktop
```
Run docker
```bash
docker compose up --build
```

### Before First Use - Understanding the Software
- Complete GEO registration following the [GEO Upload Guide](https://github.com/fgcz/geo-uploader/blob/main/documentation/GEO_instructions.md).

- For the best experience creating a new session, gather all the files into one folder, and files corresponding to the same sample should have the same prefix. It is only possible to upload files directly under the selected folder, so no multi-folder file selection is possible.

- There are 3 different accounts to be set up for this tool, do not confuse them.
  - GEO repository personal folder + password
  - GEO Uploader account login - only serves for distinguishing users
  - (Optional) MAIL configuration - for being able to register new users and receiving email notifications


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
  - Google doesn't support app passwords when the two factor authentication is not activated
  - Either turn on the two factor authentication, or skip the notifications
  - When skipping the notifications, new accounts cannot be registered, on of the default accounts has to be used for uploads.

- Cannot find the folder you are looking for on a new submission
  - Update your BASE_PATH in .flaskenv, everything is shown relative to this
  - No need to re-install, just Ctrl+C and restart the server again
  - If the path is correct, and you still can't see the folder, I suspect it has to do with the number of folders in the root.
  - In the code there is the line `max_items = 200`, if the folder has more than 100 items, it will not show the other files/directories
    - You are free to change this line in the `directory_service.py` file
- Cannot install using Makefile
  - Use the alternative version without Makefile for Windows (documented above)

- `lsof` error on Windows when running `flask start-prod` or `flask status`
  - lsof is a command only for Mac/Linux, in a Windows computer use the alternative commands to start the server
  - `flask run`

- Metadata.xlsx sheet template is deprecated, not accepted by GEO anymore.
  - Because we save a local copy of the Metadata.xlsx, whenever GEO updates their expectations, a by hand update of the file also is needed.
  - You need to update the `/geo-uploader/geo_uploader/utils/metadata_seq_template.xlsx` file with the new version
  - Also the code needs to be changed to reflect the new structure, whenever this happens, I suggest pulling the latest repository commit
  - We will keep the most recent metadata version up to date here so you don't have to.

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
