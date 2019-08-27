FROM kernsuite/base:5

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    CASA_ENABLE_TELEMETRY=false

RUN docker-apt-install casalite

WORKDIR /app
COPY check_ms.py .

