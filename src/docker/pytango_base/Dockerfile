FROM python:3.5-slim-stretch as build

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
       libboost-python-dev \
       libtango-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install pipenv

# Set up the Virtualenv
RUN python -m venv /venv

# Copy the Pipfile
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

# Install Python deps
# --deploy : so build will fail if Pipfile.lock if out of date.
# --ignore-pipfile : so it won't mess with our setup
# --dev : Install both dev and default packages
RUN pipenv install --deploy --ignore-pipfile --dev


# ==================================================================

FROM python:3.5-slim-stretch
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
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libtango9 \
        libboost-python1.62.0 \
    && rm -rf /var/lib/apt/lists/*
RUN python -m pip install pipenv
COPY --from=build /venv /venv

# Copy the Pipfile
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

## Commands executed when exending this image. Copy the Pipfile to the
## image so that pipenv knows what dependencies to install.
# ONBUILD COPY --chown=ska:ska Pipfile Pipfile
# ONBUILD COPY --chown=ska:ska Pipfile.lock Pipfile.lock
# ONBUILD RUN pipenv install --deploy --ignore-pipfile --dev
