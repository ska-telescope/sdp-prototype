# -----------------------------------------------------------------------------
# Build stage
# -----------------------------------------------------------------------------
FROM debian:buster-slim as buildenv

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

# Install packages needed to build pytango
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        python3 \
        python3-pip \
        python3-venv \
        libboost-python1.67-dev \
        libtango-dev \
        git \
    && rm -rf /var/lib/apt/lists/*

# Hack to avoid issue where PyTango cannot find libboost in default location.
RUN ln -s /usr/lib/x86_64-linux-gnu/libboost_python3-py37.so \
    /usr/lib/x86_64-linux-gnu/libboost_python-py37.so

# Install python packages
RUN python3 -m pip install pipenv wheel

# Set up the Virtualenv
RUN python3 -m venv /venv

# Install Python deps
RUN python3 -m pip install pytango==9.3.0

# -----------------------------------------------------------------------------
# Final stage
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

# Hack to avoid issue where PyTango cannot find libboost in default location.
RUN ln -s /usr/lib/x86_64-linux-gnu/libboost_python3-py37.so \
    /usr/lib/x86_64-linux-gnu/libboost_python-py37.so

RUN python3 -m pip install pipenv

# Copy virtual enviroment from build image (provides PyTango)
COPY --from=buildenv /venv /venv

