# =============================================================================
# Build layer - Extend the PyTango SKA ska base image with dev packages
# =============================================================================
ARG DOCKER_REGISTRY_USER
ARG DOCKER_REGISTRY_HOST
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango_ska_base:latest as build

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
# Final layer - Copy venv from build layer without build deps
# =============================================================================
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango_ska_base:latest

# Copy the venv from the build
COPY --from=build /venv /venv

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
