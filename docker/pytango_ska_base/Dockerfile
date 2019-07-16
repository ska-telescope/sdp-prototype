# =============================================================================
# Build layer - Extend the PyTango base image with the lmcbaseclasses package
# =============================================================================
ARG DOCKER_REGISTRY_USER
ARG DOCKER_REGISTRY_HOST
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango_base:latest as build
#FROM skaorca/pytango_base:latest as build

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN pipenv install --deploy --ignore-pipfile --dev


# =============================================================================
# Final layer - Copy venv from build layer without build deps
# =============================================================================
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango_base:latest
#FROM skaorca/pytango_base:latest

# Copy the venv from the build
COPY --from=build /venv /venv

ONBUILD COPY Pipfile Pipfile
ONBUILD COPY Pipfile.lock Pipfile.lock
