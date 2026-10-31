# Build stage: uv resolves and installs everything into /app/.venv.
# uv is pinned to the version CI uses, so the lock file is read the same way.
FROM ghcr.io/astral-sh/uv:0.13.6-python3.14-trixie-slim AS build

# Bytecode compiled at build time: the job starts faster and never writes .pyc at runtime.
# Copy mode because the cache mount below is a different filesystem than /app.
# No Python downloads: the venv must use the image's /usr/local/bin/python, which the
# runtime stage has at the same path.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencies first: this layer stays cached until pyproject.toml or uv.lock change.
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project --no-editable

# Non-editable, so the package lands in the venv and src/ is not needed at runtime.
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# Runtime stage: plain Python, no uv, no dev tools, no tests.
FROM python:3.14.4-slim-trixie

# A fixed UID makes file ownership predictable if a volume is ever mounted.
RUN groupadd --system --gid 10001 importer \
    && useradd --system --uid 10001 --gid importer --no-create-home importer

COPY --from=build /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER importer

ENTRYPOINT ["importer"]
