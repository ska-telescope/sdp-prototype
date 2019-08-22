
FROM ska-sdp-config

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

ARG HELMVER=2.14.2
RUN \
  curl https://get.helm.sh/helm-v${HELMVER}-linux-amd64.tar.gz | tar xz  && \
  mv linux-amd64/helm /usr/local/bin/helm

COPY helm_deploy.py .
CMD python helm_deploy.py
