ARG DOCKER_REGISTRY_USER
ARG DOCKER_REGISTRY_HOST

# -----------------------------------------------------------------------------
# Build stage
# -----------------------------------------------------------------------------
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango-9.3.0:buster-slim as buildenv

# Install packages needed to build pytango
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy the Pipfile
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

# Install Python deps
RUN pipenv install --deploy --ignore-pipfile --dev

# -----------------------------------------------------------------------------
# Final stage
# -----------------------------------------------------------------------------
FROM ${DOCKER_REGISTRY_HOST}/${DOCKER_REGISTRY_USER}/pytango-9.3.0:buster-slim as buildenv
WORKDIR /app
COPY --from=buldenv /venv /venv



#FROM debian:buster-slim
#
#WORKDIR /app
#
#ENV DEBIAN_FRONTEND=noninteractive \
#    LANG=C.UTF-8 \
#    LC_ALL=C.UTF-8 \
#    PYTHONDONTWRITEBYTECODE=1 \
#    PYTHONUNBUFFERED=1 \
#    PATH=/venv/bin:$PATH \
#    VIRTUAL_ENV=/venv \
#    PIPENV_VERBOSITY=-1 \
#    PIPENV_NOSPIN=1
#
## Install Python and PyTango runtime dependencies.
#RUN apt-get update \
#    && apt-get install -y --no-install-recommends \
#        python3 \
#        python3-pip \
#        libtango9 \
#        libboost-python1.67.0 \
#        make \
#    && rm -rf /var/lib/apt/lists/*
#
## Hack to avoid issue where the setup.py for PyTango cannot find libboost!
#RUN ln -s /usr/lib/x86_64-linux-gnu/libboost_python3-py37.so \
#    /usr/lib/x86_64-linux-gnu/libboost_python-py37.so
#
#RUN python3 -m pip install pipenv
#
## Copy the Pipfile
#COPY Pipfile Pipfile
#COPY Pipfile.lock Pipfile.lock
#
## Copy virtual enviroment from build image (provides PyTango)
#COPY --from=buldenv /venv /venv
#
#

