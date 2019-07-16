# =============================================================================
# Build layer - Extend the PyTango base image with the lmcbaseclasses package
# =============================================================================
FROM skaorca/pytango_base:latest as build

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN pipenv install --deploy --ignore-pipfile --dev


# =============================================================================
# Final layer - Copy venv from build layer without build deps
# =============================================================================
FROM skaorca/pytango_base:latest

# Copy the venv from the build
COPY --from=build /venv /venv

ONBUILD COPY Pipfile Pipfile
ONBUILD COPY Pipfile.lock Pipfile.lock
