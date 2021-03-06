# =============================================================================
# Pytango build image : Image that builds a venv with pytango
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

# Hack to avoid issue where the setup.py for PyTango cannot find libboost!
RUN ln -s /usr/lib/x86_64-linux-gnu/libboost_python3-py37.so \
    /usr/lib/x86_64-linux-gnu/libboost_python-py37.so
