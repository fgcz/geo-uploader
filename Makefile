# Makefile - Convenient development commands
.PHONY: setup-env setup-config setup-db flask-status install install-dev clean lint format fix help

DOCS_DIR = docs
REPORTS_DIR = reports

setup-env:
	@echo "📦 Setting up environment..."
	@bash -c '\
	if command -v mamba >/dev/null 2>&1; then \
		echo "✅ Mamba found - using mamba for faster environment creation"; \
		mamba env create -f environment.yml || echo "Environment might already exist"; \
	elif command -v conda >/dev/null 2>&1; then \
		echo "✅ Conda found - using conda for environment creation"; \
		conda env create -f environment.yml || echo "Environment might already exist"; \
	else \
		echo "❌ Neither mamba nor conda found. Please install conda or mamba first."; \
		exit 1; \
	fi'
	@conda run -n gi_geo-uploader pip install -e .

setup-config:
	@echo "⚙️  Setting up configuration..."
	cp .env.example .env
	@echo ""
	@echo "🔧 NEXT STEP: Edit .env file with your email configuration:"
	@echo "   nano .env"
	@echo "   nano .flaskenv"
	@echo ""
	@echo "💡 For Gmail: Generate App Password at https://myaccount.google.com/apppasswords"
	@echo ""
	@echo "⏭️  After editing .env .flaskenv, run: make setup-db"


setup-db:
	@echo "🗄️  Initializing database..."
	conda run -n gi_geo-uploader flask init-db
	@echo ""
	@echo "✅ Setup complete! Start the server with: make start-server"

flask-status:
	conda run -n gi_geo-uploader flask status

install:
	pip install -e .

# Install with development dependencies
install-dev:
	pip install -e ".[dev]"


# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .ruff_cache/
	rm -rf $(REPORTS_DIR)/
	rm -rf $(DOCS_DIR)/build/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Format code
format:
	ruff format geo_uploader

# Lint code
lint:
	ruff check geo_uploader || true
	mypy geo_uploader || true

fix:
	ruff check --fix geo_uploader
	ruff format geo_uploader

show-fixes:
	ruff check --diff geo_uploader

security: bandit
bandit:
	bandit -r geo_uploader/ -c pyproject.toml
security-report: bandit-report
bandit-report:
	@echo "🔍 Running Bandit security scan..."
	@mkdir -p $(REPORTS_DIR)
	bandit -r geo_uploader/ -f json -o $(REPORTS_DIR)/bandit-report.json
	bandit -r geo_uploader/ -f txt -o $(REPORTS_DIR)/bandit-report.txt
	@echo "📊 Bandit report saved to $(REPORTS_DIR)/bandit-report.{json,txt}"
# Generate reports for CI/CD
reports: security-report docs-build lint-reports
	@echo "📊 All reports generated in $(REPORTS_DIR)/ and docs/build/"

help:
	@echo "🛠️  Available commands:"
	@echo ""
	@echo "🚀 Setup & Environment:"
	@echo "  setup-env         - Set up conda environment and install package"
	@echo "  setup-config      - Copy .env.example to .env and show configuration instructions"
	@echo "  setup-db          - Initialize the database"
	@echo ""
	@echo "🖥️  Server Management:"
	@echo "  flask-status      - Check the status of Flask servers"
	@echo ""
	@echo "📦 Installation:"
	@echo "  install           - Install package in development mode"
	@echo "  install-dev       - Install with development dependencies"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  format            - Format code with ruff"
	@echo "  lint              - Run linting (ruff + mypy)"
	@echo "  fix               - Fix auto-fixable linting issues and format code"
	@echo "  show-fixes        - Show diff of what would be fixed"
	@echo ""
	@echo "🔒 Security:"
	@echo "  security          - Run bandit security scans"
	@echo "  bandit            - Run bandit security scans"
	@echo "  security-report   - Generate detailed security reports"
	@echo "  bandit-report     - Generate bandit security reports in multiple formats"
	@echo ""
	@echo "📊 Reporting:"
	@echo "  reports           - Generate all security reports"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  clean             - Remove build artifacts and cache files"
	@echo ""
	@echo "💡 Quick Start:"
	@echo "  1. make setup-env"
	@echo "  2. make setup-config  (then edit .env file)"
	@echo "  3. make setup-db"
	@echo "  4. make start-server"