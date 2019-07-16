# =============================================================================
# Build layer - Extend the PyTango SKA base image with testing packages
# =============================================================================
ARG DOCKER_REGISTRY_USER
ARG DOCKER_REGISTRY_HOST
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango_ska_base:latest as build
#FROM skaorca/pytango_ska_base:latest as build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pipenv install --deploy --ignore-pipfile --dev


# =============================================================================
# Final layer - Copy venv from build layer without build deps
# =============================================================================
#FROM skaorca/pytango_ska_base:latest
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango_ska_base:latest

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        make \
    && rm -rf /var/lib/apt/lists/*

# Copy the venv from the build
COPY --from=build /venv /venv

ONBUILD COPY Pipfile Pipfile
ONBUILD COPY Pipfile.lock Pipfile.lock
# ONBUILD RUN pipenv install --deploy --ignore-pipfile --dev
