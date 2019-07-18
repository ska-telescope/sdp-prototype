# =============================================================================
# Pytango base image : Base image providing pytango
# =============================================================================

# -----------------------------------------------------------------------------
# Build layer - This is slow as it builds pytango from source!
# Could avoid this build image if using the --target build flag
#  https://andrewlock.net/caching-docker-layers-on-serverless-build-hosts-with-multi-stage-builds---target,-and---cache-from/
# -----------------------------------------------------------------------------
ARG DOCKER_REGISTRY_USER
ARG DOCKER_REGISTRY_HOST
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango_build:latest as build

# Install python packages
RUN python3 -m pip install pipenv wheel

# Set up the Virtualenv
RUN python3 -m venv /venv

# Copy the Pipfile
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

# Install Python deps
RUN pipenv install --deploy --ignore-pipfile --dev


# -----------------------------------------------------------------------------
# Final layer
# -----------------------------------------------------------------------------
FROM debian:buster-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/venv/bin:$PATH \
    VIRTUAL_ENV=/venv \
    PIPENV_VERBOSITY=-1 \
    PIPENV_NOSPIN=1

# Install Python and PyTango runtime dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        libtango9 \
        libboost-python1.67.0 \
    && rm -rf /var/lib/apt/lists/*

# Hack to avoid issue where the setup.py for PyTango cannot find libboost!
RUN ln -s /usr/lib/x86_64-linux-gnu/libboost_python3-py37.so \
    /usr/lib/x86_64-linux-gnu/libboost_python-py37.so

RUN python3 -m pip install pipenv

COPY wait-for-it.sh /usr/local/bin/wait-for-it.sh
COPY retry.sh /usr/local/bin/retry

# Copy virtual enviroment from build image (provides PyTango)
COPY --from=build /venv /venv

# Copy the Pipfile
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

