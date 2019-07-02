FROM python:3.5-slim-stretch as build

WORKDIR /app
USER root

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/venv/bin:$PATH \
    VIRTUAL_ENV=/venv \
    PIPENV_VERBOSITY=-1 \
    PIPENV_NOSPIN=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*
RUN python -m pip install pipenv

# Copy the venv from the base image
COPY --from=skaorca/pytango_base:latest /venv /venv

# Copy the Pipfile
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

# Install Python deps
RUN pipenv install --deploy --ignore-pipfile --dev



FROM python:3.5-slim-stretch

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/venv/bin:$PATH \
    VIRTUAL_ENV=/venv \
    PIPENV_VERBOSITY=-1 \
    PIPENV_NOSPIN=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        libtango9 \
        libboost-python1.62.0 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install pipenv

# Copy the venv from the build
COPY --from=build /venv /venv

# Copy the Pipfile
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock


