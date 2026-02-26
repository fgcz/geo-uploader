FROM ghcr.io/astral-sh/uv:python3.14-trixie
COPY . /app
WORKDIR /app
RUN uv sync
ENTRYPOINT ["/app/.venv/bin/flask", "run", "-p", "8000", "--host=0.0.0.0"]
