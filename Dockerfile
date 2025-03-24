#################################################
FROM debian:bookworm-slim AS builder-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PYTHON="3.13.2" \
    UV_PYTHON_INSTALL_DIR="/app/.python" \
    UV_PYTHON_PREFERENCE="only-managed" \
    PATH="$PATH:/root/.local/bin/:/app/.venv/bin"

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    libpq-dev \
    ca-certificates \
    && groupadd --gid 1001 appuser \
    && useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser
#################################################
FROM builder-base AS python-base

WORKDIR /app

RUN apt-get install --no-install-recommends -y \
    curl \
    clang \
    && curl -LsSf https://github.com/astral-sh/uv/releases/download/0.5.29/uv-installer.sh | sh \
    && uv python install

COPY pyproject.toml ./

RUN uv sync --no-dev -n
RUN uvx --from=toml-cli toml get --toml-path=pyproject.toml project.version > .version
#################################################
FROM builder-base AS production

WORKDIR /app

RUN chown -R appuser:appuser /app

COPY --from=python-base /app/.python /app/.python
COPY --from=python-base /app/.venv /app/.venv
COPY --from=python-base /app/.version /app/
COPY /src/ /app/

USER appuser

CMD [ "python", "server.py" ]
#################################################
