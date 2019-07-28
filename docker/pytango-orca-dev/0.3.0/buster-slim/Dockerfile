ARG DOCKER_REGISTRY_USER
ARG DOCKER_REGISTRY_HOST
# =============================================================================
# Build stage
# =============================================================================
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango-9.3.0:buster-slim as buildenv

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the Pipfile
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

# Install Python deps
RUN pipenv install --deploy --ignore-pipfile --dev

# =============================================================================
# Final stage
# =============================================================================
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango-9.3.0:buster-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy the venv from the build
COPY --from=buildenv /venv /venv

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
