# =============================================================================
# Build layer - Create virtualenv, build and install pytango
# =============================================================================
FROM debian:buster-slim as build

WORKDIR /app
USER root

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/venv/bin:$PATH \
    VIRTUAL_ENV=/venv \
    PIPENV_VERBOSITY=-1 \
    PIPENV_NOSPIN=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        python3 \
        python3-pip \
        python3-venv \
        libboost-python1.67-dev \
        libtango-dev \
    && rm -rf /var/lib/apt/lists/*

# Hack to avoid issue where the setup.py for PyTango cannot find libboost!
RUN ln -s /usr/lib/x86_64-linux-gnu/libboost_python3-py37.so \
    /usr/lib/x86_64-linux-gnu/libboost_python-py37.so

RUN python3 -m pip install pipenv wheel

# Set up the Virtualenv
RUN python3 -m venv /venv

# Copy the Pipfile
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

# Install Python deps
# --deploy : so build will fail if Pipfile.lock if out of date.
# --ignore-pipfile : so it won't mess with our setup
# --dev : Install both dev and default packages
RUN pipenv install --deploy --ignore-pipfile --dev


# =============================================================================
# Final layer - Copy venv from build layer without build deps
# =============================================================================
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

RUN ln -s /usr/lib/x86_64-linux-gnu/libboost_python3-py37.so \
    /usr/lib/x86_64-linux-gnu/libboost_python-py37.so

RUN python3 -m pip install pipenv

# Copy virtual enviroment from build image (provides PyTango)
COPY --from=build /venv /venv

COPY wait-for-it.sh /usr/local/bin/wait-for-it.sh
COPY retry.sh /usr/local/bin/retry

ONBUILD COPY Pipfile Pipfile
ONBUILD COPY Pipfile.lock Pipfile.lock

